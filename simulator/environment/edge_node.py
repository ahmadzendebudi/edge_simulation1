from abc import abstractmethod
from asyncio.log import logger
import sys
from typing import Any, Callable, Sequence, Tuple
from simulator.common import Common
from simulator.config import Config
from simulator.core import Connection
from simulator.core import TaskQueue
from simulator.core import simulator
from simulator.core.parcel import Parcel
from simulator.core.parcel_queue import ParcelQueue
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.core.task import Task
from simulator.environment.task_node import TaskNode
from simulator.logger import Logger
from simulator.processes.router_edge import RouterEdge, RouterEdgePlug
from simulator.processes.task_generator import TaskGenerator
from simulator.processes.task_multiplexer import TaskMultiplexer, TaskMultiplexerPlug
from simulator.processes.parcel_transmitter import ParcelTransmitter, ParcelTransmitterPlug
from simulator.task_multiplexing.selector import TaskMultiplexerSelector
from simulator.task_multiplexing.transition import Transition
      
class EdgeNodePlug:
    @abstractmethod
    def updateEdgeNodeConnections(self, nodeId: int, nodeExternalId: int) -> Tuple[Sequence[Connection], Sequence[Connection], int]:
        '''Should return (edgeConnections, mobileConnections, duration)
        
        duration: maximum time until this function is called again, a value
        of "None" means there will not be another call to this function'''
        pass
    
class EdgeNode(TaskNode, TaskMultiplexerPlug, RouterEdgePlug):
    def __init__(self, externalId: int, plug: EdgeNodePlug, flops: int, cores: int) -> None:
        self._plug = plug
        self._edgeStatesMap = {}
        self._destEdgeId = None
        super().__init__(externalId, flops, cores)
    
    def initializeConnection(self, simulator: Simulator):
        self._simulator = simulator
        
        #router:
        self._router = RouterEdge(simulator, self.id(), self)
        simulator.registerProcess(self._router)

        edgeConnections, mobileConnections, duration = self._plug.updateEdgeNodeConnections(self.id(), self.externalId())
        self._router.updateConnections(mobileConnections, edgeConnections)
        
        if (duration != None):
            self._connectionProcess = Process()
            self._connectionProcess.wake = self.updateConnections
            simulator.registerProcess(self._connectionProcess)
            simulator.registerEvent(Common.time() + duration, self._connectionProcess.id())
    
    def updateConnections(self):
        edgeConnections, mobileConnections, duration = self._plug.updateEdgeNodeConnections(self.id(), self.externalId())
        self._router.updateConnections(mobileConnections, edgeConnections)
        
        if (duration != None):
            self._simulator.registerEvent(Common.time() + duration, self._connectionProcess.id())
        
    def initializeProcesses(self, simulator: Simulator, edgeMultiplexSelector: TaskMultiplexerSelector,
                            mobileMultiplexSelector: TaskMultiplexerSelector = None):
        super().initializeProcesses(simulator)
        
        self._multiplexSelector = edgeMultiplexSelector
        self._taskMultiplexer = TaskMultiplexer(self, edgeMultiplexSelector, self)
        simulator.registerProcess(self._taskMultiplexer)
        self._multiplexQueue = TaskQueue()
        simulator.registerTaskQueue(self._multiplexQueue)

        self._mobileMultiplexSelector = mobileMultiplexSelector
        
        self._taskIdToSenderIdMap = {}
        
        
        self._lastTransmitEmptyQueues = False
        '''indicates if the local and multiplex queues while sending the last states were empty'''
        
        self._stateTransmissionUpdate()
            
    def wake(self) -> None:
        self._stateTransmissionUpdate()
        return super().wake()

    def _stateTransmissionUpdate(self):
        if (not hasattr(self, '_lastStateTransmission') or
            Common.time() - self._lastStateTransmission >= Config.get("node_state_transmission_interval")):
            taskGeneration = Common.time() < Config.get("task_generation_duration")
            emptyQueues = self.currentWorkload() == 0 and self._multiplexQueue.qsize() == 0
            if taskGeneration or not emptyQueues or not self._lastTransmitEmptyQueues:
                self._lastTransmitEmptyQueues = emptyQueues
                self._lastStateTransmission = Common.time()
                self._simulator.registerEvent(Common.time() + Config.get("node_state_transmission_interval"), self.id())
                self._transmitNodeState()
            
    def _transmitNodeState(self):
        if Logger.levelCanLog(3):
            Logger.log("state transmission edgeId:" + str(self.id()), 3)
        
        #Transmit state   
        content = [self.id(), self.currentWorkload(), self._localQueue.qsize()]
        Logger.log("edge load: " + str(content), 2)
        size = Config.get("state_parcel_size_per_variable_in_bits") * len(content)
        for connection in self._router.getAllConnections():
            parcel = Parcel(Common.PARCEL_TYPE_NODE_STATE, size, content, self.id(), connection.destNode())
            self._router.sendParcel(parcel)
        
        #Transmit mobile ANN parameters
        if self._mobileMultiplexSelector != None:
            model = self._mobileMultiplexSelector.extractModel()
            for connection in self._router.getMobileConnections():
                parcel = Parcel(Common.PARCEL_TYPE_ANN_PARAMS, model.size, model, self.id(), connection.destNode())
                self._router.sendParcel(parcel)
        
    def _receiveParcel(self, parcel: Parcel) -> bool:
        if parcel.type == Common.PARCEL_TYPE_PACKAGE:
            pass #TODO
        elif parcel.type == Common.PARCEL_TYPE_TASK:
            task = parcel.content
            task.powerConsumed += parcel.powerConsumed
            self._multiplexQueue.put(task)
            self._simulator.registerEvent(Common.time(), self._taskMultiplexer.id())
            self._taskIdToSenderIdMap[task.id()] = parcel.senderNodeId
        elif parcel.type == Common.PARCEL_TYPE_TASK_RESULT:
            task = parcel.content
            self._taskResultsArrival(task, True)
        elif parcel.type == Common.PARCEL_TYPE_NODE_STATE:
            content = parcel.content
            self._edgeStatesMap[content[0]] = [content[1], content[2]]
        elif parcel.type == Common.PARCEL_TYPE_TRANSITION:
            transition = parcel.content
            self._mobileMultiplexSelector.addToBuffer(transition)
            #forward transition if it was received by a mobile node
            if not any(map(lambda connection: connection.destNode() == parcel.senderNodeId, self._router.getEdgeConnections())):
                for connection in self._router.getEdgeConnections():
                    parcel = Parcel(Common.PARCEL_TYPE_TRANSITION, sys.getsizeof(transition), transition, self._id, connection.destNode())
                    self._router.sendParcel(parcel)
        else:
            raise RuntimeError("Parcel type not supported for edge node")
    
    #State handler:
    
    def _updateDestEdge(self, task: Task):
        destId = None
        minValue = None
        index = 0
        if not Config.get("mode_workload_provided"):
            index = 1
        for id, value in self._edgeStatesMap.items():
                if minValue == None or minValue > value[index]:
                    minValue = value[index]
                    destId = id 
        self._destEdgeId = destId
        Logger.log("updated dest (" + str(self.id()) + "edge: id: " + str(self._destEdgeId) + " value: " + str(minValue), 3)
        #TODO Instead of workload, it should be updated whenever state is fetched
    
    def fetchState(self, task: Task, processId: int) -> Sequence[float]:
        self._updateDestEdge(task)
        edgeState = self._edgeStatesMap[self._destEdgeId]
        transmitter = self._router.getTransmitter(self._destEdgeId)
        transmitQueue = transmitter.transmitQueue()
        return self._generateState(task, self._router.getConnection(self._destEdgeId).datarate(),
                self.currentWorkload(), self._localQueue.qsize(),
                transmitter.remainingTransmitTaskWorkload(),
                transmitter.remainingTransmitSize(),
                transmitQueue.qsize(),
                edgeState[0], edgeState[1])
    
    def fetchTaskInflatedState(self, task: Task, processId: int) -> Sequence[float]:
        self._updateDestEdge(task)
        edgeState = self._edgeStatesMap[self._destEdgeId]
        taskWorkload = task.workload()
        transmitter = self._router.getTransmitter(self._destEdgeId)
        transmitQueue = transmitter.transmitQueue()
        return self._generateState(task, self._router.getConnection(self._destEdgeId).datarate(),
                self.currentWorkload() + taskWorkload, self._localQueue.qsize() + 1,
                transmitter.remainingTransmitTaskWorkload() + taskWorkload,
                transmitter.remainingTransmitSize() + task.size(),
                transmitQueue.qsize() + 1,
                edgeState[0], edgeState[1])

    def _generateState(self, task: Task, datarate: int, localWorkload: int, localQueueSize: int,
                        localTransferWorkload: int, localTransferSize: int, localTransferQueueSize: int, 
                        remoteWorkload: int, remoteQueueSize: int):
        normalTaskWorkload = TaskGenerator.normalTaskWorkload()
        normalTaskSize = TaskGenerator.normalTaskSize()
        
        if Config.get("mode_workload_provided"):
            return [task.size() / normalTaskSize, task.workload() / normalTaskWorkload, Common.time() - task.arrivalTime(),
                datarate / normalTaskSize,
                localWorkload / normalTaskWorkload, localQueueSize,
                localTransferWorkload / normalTaskWorkload, localTransferSize / normalTaskSize, localTransferQueueSize,
                remoteWorkload/normalTaskWorkload, remoteQueueSize]
        else:
            return [task.size() / normalTaskSize, Common.time() - task.arrivalTime(),
                datarate / normalTaskSize, localQueueSize,
                localTransferSize / normalTaskSize, localTransferQueueSize,
                remoteQueueSize]
        
    @classmethod
    def fetchStateShape(cls) -> Tuple[int]:
        if Config.get("mode_workload_provided"):
            return (11,)
        else:
            return (7,)
    
    def recordTransition(self, task: Task, state1, state2, actionObject) -> None:
        if (self._transitionRecorder != None):
            transition = Transition(task.id(), state1, state2, actionObject, self._multiplexSelector.rewardFunction(),
                                    taskWorkload=task.workload())
            self._transitionRecorder.put(transition)

    #Task multiplexer
    def fetchMultiplexerQueue(self, processId: int) -> TaskQueue:
        return self._multiplexQueue
    
    def taskLocalExecution(self, task: Task, processId: int) -> None:
        self._localQueue.put(task)
        for taskRunner in self._taskRunners:
            self._simulator.registerEvent(Common.time(), taskRunner.id())
    
    def taskTransimission(self, task: Task, processId: int, destinationId: int) -> None:
        parcel = Parcel(Common.PARCEL_TYPE_TASK, task.size(), task, self._id, self._destEdgeId)
        self._router.sendParcel(parcel)
        
    
    #Task Runner
    def taskRunComplete(self, task: Task, processId: int):
        recordTransitionCompletion = task.hopLimit() == 1
        self._taskResultsArrival(task, recordTransitionCompletion)
    
    def _taskResultsArrival(self, task: Task, recordTransitionCompletion = False):
        if recordTransitionCompletion:
            delay = Common.time() - task.arrivalTime()
            transition = self._transitionRecorder.completeTransition(task.id(), delay, task.powerConsumed)
            self._multiplexSelector.addToBuffer(transition)
        taskSenderNodeId = self._taskIdToSenderIdMap.pop(task.id())
        size = Config.get("task_result_parcel_size_in_bits")
        parcel = Parcel(Common.PARCEL_TYPE_TASK_RESULT, size, task, self.id(), taskSenderNodeId)
        self._router.sendParcel(parcel)
    
    #Router
    def isNodeOfInterest(self, nodeId) -> bool:
        raise "Not implemented"#TODO

    def receiveRoutedParcel(self, parcel: Parcel):
        self._receiveParcel(parcel)

    def wakeTaskRunnerAt(self, time: int, processId: int):
        return super().wakeTaskRunnerAt(time, processId)
    