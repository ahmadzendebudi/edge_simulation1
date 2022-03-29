from abc import abstractmethod
from typing import Sequence, Tuple
from simulator.common import Common
from simulator.core import Node
from simulator.core import Connection
from simulator.core import TaskQueue
from simulator.core.parcel import Parcel
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.core.task import Task
from simulator.environment.parcel_types import ParcelTypes
from simulator.logger import Logger
from simulator.processes.task_multiplexer import TaskMultiplexer, TaskMultiplexerPlug, TaskMultiplexerSelectorLocal, TaskMultiplexerSelectorRandom
from simulator.processes.task_runner import TaskRunner, TaskRunnerPlug
from simulator.processes.task_transmitter import TaskTransmitter, TaskTransmitterPlug

class EdgeNodePlug:
    @abstractmethod
    def updateEdgeNodeConnections(self, nodeId: int, nodeExternalId: int) -> Tuple[Sequence[Connection], Sequence[Connection], int]:
        '''Should return (edgeConnections, mobileConnections, duration)
        
        duration: maximum time until this function is called again, a value
        of "None" means the will not be another call to this function'''
        pass
    
class EdgeNode(Node, TaskMultiplexerPlug, TaskRunnerPlug, TaskTransmitterPlug):
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
        self._edgeConnectionMap = {}
        for edgeConnection in self._edgeConnections:
            self._edgeConnectionMap[edgeConnection.destNode()] = edgeConnection
    
    def updateConnections(self):
        self._edgeConnections, self._mobileConnections, duration = self._plug.updateEdgeNodeConnections(self.id(), self.externalId())
        if (duration != None):
            self._simulator.registerEvent(Common.time() + duration, self._connectionProcess.id())
        
    def initializeProcesses(self, simulator: Simulator):
        self._simulator = simulator
        
        #TODO local selector should be replaced with DRL selector
        multiplex_selector = TaskMultiplexerSelectorRandom(list(self._edgeConnectionMap.keys()))
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
        self._transmitQueueMap = {}
        self._transmitterMap = {}
        self._transmitterIdToDestNodeIdMap = {}
        for edgeId in self._edgeConnectionMap.keys():
            transmitQueue = TaskQueue()
            transmitter = TaskTransmitter(self)
            
            simulator.registerTaskQueue(transmitQueue)
            simulator.registerProcess(transmitter)
            
            self._transmitQueueMap[edgeId] = transmitQueue
            self._transmitterMap[edgeId] = transmitter
            
            self._transmitterIdToDestNodeIdMap[transmitter.id()] = edgeId
            
            
        
    
    def _receiveParcel(self, parcel: Parcel) -> bool:
        if parcel.type == ParcelTypes.PARCEL_TYPE_TASK:
            task = parcel.task
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
        transmitterQueue = self._transmitQueueMap[destinationId]
        transmitterQueue.put(task)
        transmitter = self._transmitterMap[destinationId]
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
    
    def fetchTaskTransmitterQueue(self, processId: int) -> TaskQueue:
        destNodeId = self._transmitterIdToDestNodeIdMap[processId]
        return self._transmitQueueMap[destNodeId]
    
    def fetchDestinationConnection(self, processId: int) -> Connection:
        destNodeId = self._transmitterIdToDestNodeIdMap[processId]
        return self._edgeConnectionMap[destNodeId]
    
    def taskTransmissionComplete(self, task: Task, processId: int) -> int:
        parcel = Parcel(ParcelTypes.PARCEL_TYPE_TASK, self.id())
        parcel.task = task
        destNodeId = self._transmitterIdToDestNodeIdMap[processId]
        self._simulator.sendParcel(parcel, destNodeId)
    
    def wakeTaskTransmitterAt(self, time: int, processId: int) -> None:
        self._simulator.registerEvent(time, processId)