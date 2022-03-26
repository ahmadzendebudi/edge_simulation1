from simulator.common import Common
from simulator.core.node import Node
from simulator.core.connection import Connection
from simulator.core.parcel import Parcel
from simulator.core.simulator import Simulator
from simulator.core.task_queue import TaskQueue
from simulator.core.task import Task
from simulator.processes.task_distributer import TaskDistributer, TaskDistributerPlug
from simulator.processes.task_generator import TaskGenerator, TaskGeneratorPlug
from simulator.processes.task_multiplexer import TaskMultiplexer, TaskMultiplexerPlug, TaskMultiplexerSelectorRandom
from simulator.processes.task_runner import TaskRunner, TaskRunnerPlug
from simulator.processes.task_transmitter import TaskTransmitter, TaskTransmitterPlug

class MobileNode(Node, TaskDistributerPlug, TaskGeneratorPlug, TaskMultiplexerPlug,
                 TaskRunnerPlug, TaskTransmitterPlug):
    def __init__(self, id, edgeConnection: Connection) -> None:
        self._edgeConnection = edgeConnection
        super().__init__(id)
    
    def edgeConnection(self) -> Connection:
        self._edgeConnection
    
    def setup(self, simulator: Simulator):
        self._simulator = simulator
        
        self._taskDistributer = TaskDistributer(self)
        simulator.registerProcess(self._taskDistributer)
        simulator.registerEvent(Common.time(), self._taskDistributer.id())
        
        self._taskGenerator = TaskGenerator(self)
        simulator.registerProcess(self._taskGenerator)
        
        #TODO random selector should be replaced with DRL selector
        multiplex_selector = TaskMultiplexerSelectorRandom([self.edgeConnection().destNode()])
        self._taskMultiplexer = TaskMultiplexer(self, multiplex_selector)
        simulator.registerProcess(self._taskMultiplexer)
        self._multiplexQueue = TaskQueue(self._taskMultiplexer.id())
        simulator.registerTaskQueue(self._multiplexQueue)
        
        self._taskRunner = TaskRunner(self)
        simulator.registerProcess(self._taskRunner)
        self._localQueue = TaskQueue(self._taskRunner.id())
        simulator.registerTaskQueue(self._localQueue)
        
        self._taskTransmitter = TaskTransmitter(self)
        simulator.registerProcess(self._taskTransmitter)
        self._transmitQueue = TaskQueue(self._taskTransmitter.id())
        simulator.registerTaskQueue(self._transmitQueue)
    
    def registerTask(self, time: int, processId: int) -> None:
        self._simulator.registerEvent(time, self._taskGenerator.id())
    
    def wakeTaskDistributerAt(self, time: int, processId: int) -> None:
        self._simulator.registerEvent(time, self._taskDistributer.id())
    
    def taskNodeId(self, processId: int) -> int:
        return self._id
    
    def taskArrival(self, task: Task, processId: int) -> None:
        self._simulator.registerTask(task)
        self._multiplexQueue.put(task)
        self._simulator.registerEvent(Common.time(), self._taskMultiplexer.id())
    
    def taskLocalExecution(self, task: Task, processId: int) -> None:
        self._localQueue.put(task)
        self._simulator.registerEvent(Common.time(), self._taskRunner.id())
    
    def taskTransimission(self, task: Task, processId: int, destinationId: int) -> None:
        self._transmitQueue.put(task)
        self._simulator.registerEvent(Common.time(), self._taskTransmitter.id())
    
    def fetchTaskRunnerQueue(self, processId: int) -> TaskQueue:
        return self._localQueue
    
    def wakeTaskRunnerAt(self, time: int, processId: int):
        self._simulator.registerEvent(time, processId)
    
    def taskRunComplete(self, task: Task, processId: int):
        #TODO
        pass
    
    def fetchTaskTransmitterQueue(self, processId: int) -> TaskQueue:
        return self._transmitQueue
    
    def fetchDestinationConnection(self, processId: int) -> Connection:
        return self.edgeConnection()
    
    def taskTransmissionComplete(self, task: Task, processId: int) -> int:
        destNodeId = self.edgeConnection().destNode()
        self._simulator.sendParcel()
        pass
    
    def wakeTaskTransmitterAt(self, time: int, processId: int) -> None:
        self._simulator.registerEvent(time, self._taskTransmitter.id())
        
    def _receiveParcel(self, parcel: Parcel) -> bool:
        raise RuntimeError("mobile node does not recieve parcels")
    
    