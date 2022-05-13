from abc import abstractmethod
from typing import Any, Callable, Sequence, Tuple
from simulator.common import Common
from simulator.config import Config
from simulator.core import Connection
from simulator.core import TaskQueue
from simulator.core.parcel import Parcel
from simulator.core.parcel_queue import ParcelQueue
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.core.task import Task
from simulator.environment.task_node import TaskNode
from simulator.logger import Logger
from simulator.processes.task_multiplexer import TaskMultiplexer, TaskMultiplexerPlug
from simulator.processes.parcel_transmitter import ParcelTransmitter, ParcelTransmitterPlug
from simulator.task_multiplexing.selector import TaskMultiplexerSelector
      
class EdgeNodePlug:
    @abstractmethod
    def updateEdgeNodeConnections(self, nodeId: int, nodeExternalId: int) -> Tuple[Sequence[Connection], Sequence[Connection], int]:
        '''Should return (edgeConnections, mobileConnections, duration)
        
        duration: maximum time until this function is called again, a value
        of "None" means the will not be another call to this function'''
        pass
    
class EdgeNode(TaskNode, TaskMultiplexerPlug, ParcelTransmitterPlug):
    def __init__(self, externalId: int, plug: EdgeNodePlug, flops: int, cores: int) -> None:
        self._plug = plug
        self._edgeStatesMap = {}
        self._destEdgeId = None
        super().__init__(externalId, flops, cores)
    
    def initializeConnection(self, simulator: Simulator):
        self._simulator = simulator
        self._edgeConnections, self._mobileConnections, duration = self._plug.updateEdgeNodeConnections(self.id(), self.externalId())
        self._connectionProcess = Process()
        self._connectionProcess.wake = self.updateConnections
        simulator.registerProcess(self._connectionProcess)
        if (duration != None):
            simulator.registerEvent(Common.time() + duration, self._connectionProcess.id())
        
        self._nodeConnectionMap = {}
        for connection in (self._edgeConnections + self._mobileConnections):
            self._nodeConnectionMap[connection.destNode()] = connection
    
    def updateConnections(self):
        self._edgeConnections, self._mobileConnections, duration = self._plug.updateEdgeNodeConnections(self.id(), self.externalId())
        if (duration != None):
            self._simulator.registerEvent(Common.time() + duration, self._connectionProcess.id())
        
    def initializeProcesses(self, simulator: Simulator, multiplexSelector: TaskMultiplexerSelector):
        super().initializeProcesses(simulator)
        
        self._taskMultiplexer = TaskMultiplexer(self, multiplexSelector, self)
        simulator.registerProcess(self._taskMultiplexer)
        self._multiplexQueue = TaskQueue()
        simulator.registerTaskQueue(self._multiplexQueue)
        
        self._taskIdToSenderIdMap = {}
        
        #transmitter processes:
        self._transmitterMap = {}
        self._transmitterIdToDestNodeIdMap = {}
        for nodeId in self._nodeConnectionMap.keys():
            transmitQueue = ParcelQueue()
            simulator.registerParcelQueue(transmitQueue)
            
            transmitter = ParcelTransmitter(self._simulator, transmitQueue, self)
            simulator.registerProcess(transmitter)
            
            self._transmitterMap[nodeId] = transmitter
            
            self._transmitterIdToDestNodeIdMap[transmitter.id()] = nodeId
        
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
            
        content = [self.id(), self.currentWorkload(), self._localQueue.qsize()]
        Logger.log("edge load: " + str(content), 2)
        size = Config.get("state_parcel_size_per_variable_in_bits") * len(content)
        parcel = Parcel(Common.PARCEL_TYPE_NODE_STATE, size, content, self.id())
        for destId in self._nodeConnectionMap.keys():
            transmitter = self._transmitterMap[destId]
            transmitter.transmitQueue().put(parcel)
            self._simulator.registerEvent(Common.time(), transmitter.id())
        
    def _receiveParcel(self, parcel: Parcel) -> bool:
        if parcel.type == Common.PARCEL_TYPE_TASK:
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
        else:
            raise RuntimeError("Parcel type not supported for edge node")
            
    #State handler:
    
    def _updateDestEdge(self, task: Task):
        destId = None
        minWorkload = None
        for id, value in self._edgeStatesMap.items():
            if minWorkload == None or minWorkload > value[0]:
                destId = id
        self._destEdgeId = destId
        #TODO Instead of workload, it should be updated whenever state is fetched
    
    def fetchState(self, task: Task, processId: int) -> Sequence[float]:
        self._updateDestEdge(task)
        edgeState = self._edgeStatesMap[self._destEdgeId]
        transmitter = self._transmitterMap[self._destEdgeId]
        transmitQueue = transmitter.transmitQueue()
        return self._generateState(task, self._nodeConnectionMap[self._destEdgeId].datarate(),
                self.currentWorkload(), self._localQueue.qsize(),
                transmitter.remainingTransmitWorkload(),
                transmitter.remainingTransmitSize(),
                transmitQueue.qsize(),
                edgeState[0], edgeState[1])
    
    def fetchTaskInflatedState(self, task: Task, processId: int) -> Sequence[float]:
        self._updateDestEdge(task)
        edgeState = self._edgeStatesMap[self._destEdgeId]
        taskWorkload = task.size() * task.workload()
        transmitter = self._transmitterMap[self._destEdgeId]
        transmitQueue = transmitter.transmitQueue()
        return self._generateState(task, self._nodeConnectionMap[self._destEdgeId].datarate(),
                self.currentWorkload() + taskWorkload, self._localQueue.qsize() + 1,
                transmitter.remainingTransmitWorkload() + taskWorkload,
                transmitter.remainingTransmitSize() + task.size(),
                transmitQueue.qsize() + 1,
                edgeState[0], edgeState[1])

    def _generateState(self, task: Task, datarate: int, localWorkload: int, localQueueSize: int,
                        localTransferWorkload: int, localTransferSize: int, localTransferQueueSize: int, 
                        remoteWorkload: int, remoteQueueSize: int):
        normalTaskWorkload = Config.get("task_size_kBit") * Config.get("task_kflops_per_bit") * 10 ** 6
        normalTaskSize = 10 ** 6
        
        if Config.get("mode_workload_provided"):
            return [task.size() / normalTaskSize, task.size() * task.workload() / normalTaskWorkload, Common.time() - task.arrivalTime(),
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
    
    #Task multiplexer
    def fetchMultiplexerQueue(self, processId: int) -> TaskQueue:
        return self._multiplexQueue
    
    def taskLocalExecution(self, task: Task, processId: int) -> None:
        self._localQueue.put(task)
        for taskRunner in self._taskRunners:
            self._simulator.registerEvent(Common.time(), taskRunner.id())
    
    def taskTransimission(self, task: Task, processId: int, destinationId: int) -> None:
        transmitter = self._transmitterMap[self._destEdgeId]
        parcel = Parcel(Common.PARCEL_TYPE_TASK, task.size(), task, self._id, task.size() * task.workload())
        transmitter.transmitQueue().put(parcel)
        self._simulator.registerEvent(Common.time(), transmitter.id())
        #approximating the work load in edge by adding the current task to the last state report of said edge:
        #No longer needed as the transmitter metrics are included in state
        #edgeState = self._edgeStatesMap[self._destEdgeId]
        #self._edgeStatesMap[self._destEdgeId] = [edgeState[0] + task.size() * task.workload(), edgeState[1] + 1]
        
    
    #Task Runner
    def taskRunComplete(self, task: Task, processId: int):
        recordTransitionCompletion = task.hopLimit == 1
        self._taskResultsArrival(task, recordTransitionCompletion)
    
    def _taskResultsArrival(self, task: Task, recordTransitionCompletion = False):
        if recordTransitionCompletion: #TODO dql selector should be unique to each edge, to be implemented
            delay = Common.time() - task.arrivalTime()
            self._transitionRecorder.completeTransition(task.id(), delay, task.powerConsumed)
        
        taskSenderNodeId = self._taskIdToSenderIdMap.pop(task.id())
        size = Config.get("task_result_parcel_size_in_bits")
        parcel = Parcel(Common.PARCEL_TYPE_TASK_RESULT, size, task, self.id())
        transmitter = self._transmitterMap[taskSenderNodeId]
        transmitter.transmitQueue().put(parcel)
        self._simulator.registerEvent(Common.time(), transmitter.id())
    
    #Task transmission    
    def fetchDestinationConnection(self, processId: int) -> Connection:
        destNodeId = self._transmitterIdToDestNodeIdMap[processId]
        return self._nodeConnectionMap[destNodeId]
    
    def parcelTransmissionComplete(self, task: Task, processId: int) -> int:
        pass #Nothing to do here, I can add a log if needed
    
    
    
    def wakeTaskRunnerAt(self, time: int, processId: int):
        return super().wakeTaskRunnerAt(time, processId)
    