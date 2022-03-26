from typing import Sequence
from simulator.common import Common
from simulator.core import Node
from simulator.core import Connection
from simulator.core import TaskQueue
from simulator.core.parcel import Parcel
from simulator.core.simulator import Simulator
from simulator.core.task import Task
from simulator.processes.task_multiplexer import TaskMultiplexer, TaskMultiplexerPlug, TaskMultiplexerSelectorLocal
from simulator.processes.task_runner import TaskRunner, TaskRunnerPlug

class EdgeNode(Node, TaskMultiplexerPlug, TaskRunnerPlug):
    PARCEL_TYPE_TASK = "edgeNodeParcel/Task"
    '''The parcel must include a variable containing the task with name "task"'''
    
    def __init__(self, id: int, edgeConnections: Sequence[Connection],
                 mobileDeviceConnections: Sequence[Connection]) -> None:
        self._edgeConnections = edgeConnections
        self._mobileDeviceConnections = mobileDeviceConnections
        super().__init__(id)
    
    def edgeConnections(self) -> Sequence[Connection]:
        self._edgeConnections
    
    def mobileDeviceConnections(self) -> Sequence[Connection]:
        self._mobileDeviceConnections
        
    def setup(self, simulator: Simulator):
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
        if parcel.type == self.PARCEL_TYPE_TASK:
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