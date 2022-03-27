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
from simulator.processes.task_multiplexer import TaskMultiplexer, TaskMultiplexerPlug, TaskMultiplexerSelectorLocal
from simulator.processes.task_runner import TaskRunner, TaskRunnerPlug

class EdgeNodePlug:
    @abstractmethod
    def updateEdgeNodeConnections(self, nodeId: int, nodeExternalId: int) -> Tuple[Sequence[Connection], Sequence[Connection], int]:
        '''Should return (edgeConnections, mobileConnections, duration)
        
        duration: maximum time until this function is called again, a value
        of "None" means the will not be another call to this function'''
        pass
    
class EdgeNode(Node, TaskMultiplexerPlug, TaskRunnerPlug):
    def __init__(self, externalId: int, plug: EdgeNodePlug) -> None:
        self._plug = plug
        super().__init__(externalId)
    
    def initializeConnection(self, simulator: Simulator):
        self._simulator = simulator
        self._edgeConnections, self._mobileConnections, duration = self._plug.updateEdgeNodeConnections(self.id(), self.externalId())
        self._connectionProcess = Process()
        self._connectionProcess.wake = self.updateConnections
        simulator.registerProcess(self._connectionProcess)
        if (duration != None):
            simulator.registerEvent(Common.time() + duration, self._connectionProcess.id())
    
    def updateConnections(self):
        self._edgeConnections, self._mobileConnections, duration = self._plug.updateEdgeNodeConnections(self.id(), self.externalId())
        if (duration != None):
            self._simulator.registerEvent(Common.time() + duration, self._connectionProcess.id())
        
    def initializeProcesses(self, simulator: Simulator):
        self._simulator = simulator
        
        #TODO local selector should be replaced with DRL selector
        multiplex_selector = TaskMultiplexerSelectorLocal()
        self._taskMultiplexer = TaskMultiplexer(self, multiplex_selector)
        simulator.registerProcess(self._taskMultiplexer)
        self._multiplexQueue = TaskQueue(self._taskMultiplexer.id())
        simulator.registerTaskQueue(self._multiplexQueue)
        
        self._taskRunner = TaskRunner(self)
        simulator.registerProcess(self._taskRunner)
        self._localQueue = TaskQueue(self._taskRunner.id())
        simulator.registerTaskQueue(self._localQueue)
        
    
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
        self._simulator.registerEvent(Common.time(), self._taskRunner.id())
    
    def taskTransimission(self, task: Task, processId: int, destinationId: int) -> None:
        #TODO
        raise NotImplementedError("not implemented yet")
    
    def fetchTaskRunnerQueue(self, processId: int) -> TaskQueue:
        return self._localQueue
    
    def wakeTaskRunnerAt(self, time: int, processId: int):
        self._simulator.registerEvent(time, processId)
    
    def taskRunComplete(self, task: Task, processId: int):
        #TODO
        pass