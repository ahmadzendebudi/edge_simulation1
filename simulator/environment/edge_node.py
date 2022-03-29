from abc import abstractmethod
from typing import Sequence, Tuple
import simulator
from simulator.common import Common
from simulator.config import Config
from simulator.core import Node
from simulator.core import Connection
from simulator.core import TaskQueue
from simulator.core.parcel import Parcel
from simulator.core.parcel_queue import ParcelQueue
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.core.task import Task
from simulator.logger import Logger
from simulator.processes.task_multiplexer import TaskMultiplexer, TaskMultiplexerPlug, TaskMultiplexerSelectorLocal, TaskMultiplexerSelectorRandom
from simulator.processes.task_runner import TaskRunner, TaskRunnerPlug
from simulator.processes.parcel_transmitter import ParcelTransmitter, ParcelTransmitterPlug

class EdgeNodePlug:
    @abstractmethod
    def updateEdgeNodeConnections(self, nodeId: int, nodeExternalId: int) -> Tuple[Sequence[Connection], Sequence[Connection], int]:
        '''Should return (edgeConnections, mobileConnections, duration)
        
        duration: maximum time until this function is called again, a value
        of "None" means the will not be another call to this function'''
        pass
    
class EdgeNode(Node, TaskMultiplexerPlug, TaskRunnerPlug, ParcelTransmitterPlug):
    def __init__(self, externalId: int, plug: EdgeNodePlug, flops: int, cores: int) -> None:#TODO in case of multicore, we should have multiple task runners
        self._plug = plug
        self._flops = flops
        self._cores = cores
        super().__init__(externalId)
    
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
        
    def initializeProcesses(self, simulator: Simulator):
        self._simulator = simulator
        
        #TODO -->local selector should be replaced with DRL selector
        edgeDestNodeIds = []
        for connection in self._edgeConnections:
            edgeDestNodeIds.append(connection.destNode())
        multiplex_selector = TaskMultiplexerSelectorRandom(edgeDestNodeIds)
        #<--
        self._taskMultiplexer = TaskMultiplexer(self, multiplex_selector)
        simulator.registerProcess(self._taskMultiplexer)
        self._multiplexQueue = TaskQueue()
        simulator.registerTaskQueue(self._multiplexQueue)
        
        #local task runner processes:
        self._localQueue = TaskQueue()
        simulator.registerTaskQueue(self._localQueue)
        self._taskRunners = []
        for _ in range(0, self._cores):
            taskRunner = TaskRunner(self, self._flops)
            simulator.registerProcess(taskRunner)
            self._taskRunners.append(taskRunner)
        
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
            emptyQueues = self._currentWorkload() == 0 and self._multiplexQueue.qsize() == 0
            if taskGeneration or not emptyQueues or not self._lastTransmitEmptyQueues:
                if emptyQueues:
                    self._lastTransmitEmptyQueues = True
                self._lastStateTransmission = Common.time()
                self._simulator.registerEvent(Common.time() + Config.get("node_state_transmission_interval"), self.id())
            self._transmitNodeState()
            
    def _transmitNodeState(self):
        if Logger.levelCanLog(3):
            Logger.log("state transmission edgeId:" + str(self.id()), 3)
            
        content = [self.id, self._currentWorkload(), self._localQueue.qsize()]
        size = Config.get("state_parcel_size_per_variable_in_bits") * len(content)
        parcel = Parcel(Common.PARCEL_TYPE_NODE_STATE, size, content, self.id())
        
        for mobileConnection in self._mobileConnections:
            transmitter = self._transmitterMap[mobileConnection.destNode()]
            transmitter.transmitQueue().put(parcel)
            self._simulator.registerEvent(Common.time(), transmitter.id())
        
    def _currentWorkload(self):
        workload = TaskRunner.remainingWorkloadTaskQueue(self._localQueue)
        for taskRunner in self._taskRunners:
            workload += taskRunner.remainingWorkloadForCurrentTask()
        return workload
    
    def _receiveParcel(self, parcel: Parcel) -> bool:
        if parcel.type == Common.PARCEL_TYPE_TASK:
            task = parcel.content
            self._multiplexQueue.put(task)
            self._simulator.registerEvent(Common.time(), self._taskMultiplexer.id())
        else:
            raise RuntimeError("Parcel type not supported for edge node")
    
    def fetchMultiplexerQueue(self, processId: int) -> TaskQueue:
        return self._multiplexQueue
    
    def taskLocalExecution(self, task: Task, processId: int) -> None:
        self._localQueue.put(task)
        for taskRunner in self._taskRunners:
            self._simulator.registerEvent(Common.time(), taskRunner.id())
    
    def taskTransimission(self, task: Task, processId: int, destinationId: int) -> None:
        transmitter = self._transmitterMap[destinationId]
        parcel = Parcel(Common.PARCEL_TYPE_TASK, task.size(), task, self._id)
        transmitter.transmitQueue().put(parcel)
        self._simulator.registerEvent(Common.time(), transmitter.id())
    
    def fetchTaskRunnerQueue(self, processId: int) -> TaskQueue:
        return self._localQueue
    
    def wakeTaskRunnerAt(self, time: int, processId: int):
        self._simulator.registerEvent(time, processId)
    
    def taskRunComplete(self, task: Task, processId: int):
        #TODO
        if Logger.levelCanLog(2):
            Logger.log("edge execution completed: " + str(task), 2)
        pass
    
    def fetchDestinationConnection(self, processId: int) -> Connection:
        destNodeId = self._transmitterIdToDestNodeIdMap[processId]
        return self._nodeConnectionMap[destNodeId]
    
    def parcelTransmissionComplete(self, task: Task, processId: int) -> int:
        pass #Nothing to do here, I can add a log if needed