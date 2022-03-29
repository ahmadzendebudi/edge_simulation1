from abc import abstractmethod
from collections import deque
from typing import Tuple
from simulator.common import Common
from simulator.core.node import Node
from simulator.core.connection import Connection
from simulator.core.parcel import Parcel
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.core.task_queue import TaskQueue
from simulator.core.task import Task
from simulator.environment.parcel_types import ParcelTypes
from simulator.logger import Logger
from simulator.processes.task_distributer import TaskDistributer, TaskDistributerPlug
from simulator.processes.task_generator import TaskGenerator, TaskGeneratorPlug
from simulator.processes.task_multiplexer import TaskMultiplexer, TaskMultiplexerPlug, TaskMultiplexerSelectorRandom
from simulator.processes.task_runner import TaskRunner, TaskRunnerPlug
from simulator.processes.task_transmitter import TaskTransmitter, TaskTransmitterPlug

class MobileNodePlug:
    @abstractmethod
    def updateMobileNodeConnection(self, nodeId: int, nodeExternalId: int) -> Tuple[Connection, int]:
        '''Should return the current connection and the maximum duration before which
        this function is called again'''
        pass
    
class MobileNode(Node, TaskDistributerPlug, TaskGeneratorPlug, TaskMultiplexerPlug,
                 TaskRunnerPlug, TaskTransmitterPlug):
    def __init__(self, externalId: int, plug: MobileNodePlug, flops: int, cores: int) -> None:#TODO a parameter for cpu cycles per second
        self._plug = plug
        self._flops = flops
        self._cores = cores
        super().__init__(externalId)
    
    def edgeConnection(self) -> Connection:
        self._edgeConnection
    
    def initializeConnection(self, simulator: Simulator):
        self._simulator = simulator
        self._edgeConnection, duration = self._plug.updateMobileNodeConnection(self.id(), self.externalId())
        self._connectionProcess = Process()
        self._connectionProcess.wake = self.updateConnection
        simulator.registerProcess(self._connectionProcess)
        if (duration != None):
            simulator.registerEvent(Common.time() + duration, self._connectionProcess.id())
    
    def updateConnection(self):
        self._edgeConnection, duration = self._plug.updateMobileNodeConnection(self.id(), self.externalId())
        if (duration != None):
            self._simulator.registerEvent(Common.time() + duration, self._connectionProcess.id())
        
    def initializeProcesses(self, simulator: Simulator):
        self._simulator = simulator
        
        self._taskDistributer = TaskDistributer(self)
        simulator.registerProcess(self._taskDistributer)
        simulator.registerEvent(Common.time(), self._taskDistributer.id())
        
        self._taskDistributionTimeQueue = deque()
        self._taskGenerator = TaskGenerator(self)
        simulator.registerProcess(self._taskGenerator)
        
        #TODO random selector should be replaced with DRL selector
        multiplex_selector = TaskMultiplexerSelectorRandom([self._edgeConnection.destNode()])
        self._taskMultiplexer = TaskMultiplexer(self, multiplex_selector)
        simulator.registerProcess(self._taskMultiplexer)
        self._multiplexQueue = TaskQueue()
        simulator.registerTaskQueue(self._multiplexQueue)
        
        self._localQueue = TaskQueue()
        simulator.registerTaskQueue(self._localQueue)
        self._taskRunners = []
        for _ in range(0, self._cores):
            taskRunner = TaskRunner(self, self._flops)
            simulator.registerProcess(taskRunner)
            self._taskRunners.append(taskRunner)
        
        self._taskTransmitter = TaskTransmitter(self)
        simulator.registerProcess(self._taskTransmitter)
        self._transmitQueue = TaskQueue()
        simulator.registerTaskQueue(self._transmitQueue)
    
    def registerTask(self, time: int, processId: int) -> None:
        self._taskDistributionTimeQueue.append(time)
        self._simulator.registerEvent(time, self._taskGenerator.id())
    
    def wakeTaskDistributerAt(self, time: int, processId: int) -> None:
        self._simulator.registerEvent(time, self._taskDistributer.id())
    
    def fetchTaskDistributionTimeQueue(self, processId: int) -> deque:
        return self._taskDistributionTimeQueue
    
    def taskNodeId(self, processId: int) -> int:
        return self._id
    
    def taskArrival(self, task: Task, processId: int) -> None:
        self._simulator.registerTask(task)
        self._multiplexQueue.put(task)
        self._simulator.registerEvent(Common.time(), self._taskMultiplexer.id())
    
    def fetchMultiplexerQueue(self, processId: int) -> TaskQueue:
        return self._multiplexQueue
    
    def taskLocalExecution(self, task: Task, processId: int) -> None:
        self._localQueue.put(task)
        for taskRunner in self._taskRunners:
            self._simulator.registerEvent(Common.time(), taskRunner.id())
    
    def taskTransimission(self, task: Task, processId: int, destinationId: int) -> None:
        self._transmitQueue.put(task)
        self._simulator.registerEvent(Common.time(), self._taskTransmitter.id())
    
    def fetchTaskRunnerQueue(self, processId: int) -> TaskQueue:
        return self._localQueue
    
    def wakeTaskRunnerAt(self, time: int, processId: int):
        self._simulator.registerEvent(time, processId)
    
    def taskRunComplete(self, task: Task, processId: int):
        #TODO
        if Logger.levelCanLog(2):
            Logger.log("local execution completed: " + str(task), 2)
        pass
    
    def fetchTaskTransmitterQueue(self, processId: int) -> TaskQueue:
        return self._transmitQueue
    
    def fetchDestinationConnection(self, processId: int) -> Connection:
        return self._edgeConnection
    
    def taskTransmissionComplete(self, task: Task, processId: int) -> int:
        parcel = Parcel(ParcelTypes.PARCEL_TYPE_TASK, self.id())
        parcel.task = task
        destNodeId = self._edgeConnection.destNode()
        self._simulator.sendParcel(parcel, destNodeId)
    
    def wakeTaskTransmitterAt(self, time: int, processId: int) -> None:
        self._simulator.registerEvent(time, self._taskTransmitter.id())
        
    def _receiveParcel(self, parcel: Parcel) -> bool:
        raise RuntimeError("mobile node does not recieve parcels")
    
    