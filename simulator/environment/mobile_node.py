from simulator.core.node import Node
from simulator.core.connection import Connection
from simulator.core.simulator import Simulator
from simulator.core.task_queue import TaskQueue
from simulator.core.task import Task
from simulator.processes.mobile.task_distributer import TaskDistributer, TaskDistributerPlug
from simulator.processes.mobile.task_generator import TaskGenerator, TaskGeneratorPlug
from simulator.processes.mobile.task_multiplexer import TaskMultiplexer, TaskMultiplexerPlug

class MobileNode(Node, TaskDistributerPlug, TaskGeneratorPlug, TaskMultiplexerPlug):
    def __init__(self, id, edgeConnection: Connection) -> None:
        self._edgeConnection = edgeConnection
        super().__init__(id)
    
    def edgeConnection(self) -> Connection:
        self._edgeConnection
    
    def setup(self, simulator: Simulator):
        self._simulator = simulator
        
        self._taskDistributer = TaskDistributer(self)
        simulator.registerProcess(self._taskDistributer)
        
        self._taskGenerator = TaskGenerator(self)
        simulator.registerProcess(self._taskGenerator)
        
        self._taskMultiplexer = TaskMultiplexer(self)
        simulator.registerProcess(self._taskMultiplexer)
        self._multiplexQueue = TaskQueue(self._taskMultiplexer.id)
        
        #self._localQueue = TaskQueue(taskQueuePlug)
        #self._TransmitQueue = TaskQueue(taskQueuePlug)
    
    def registerTask(self, time: int) -> None:
        self._simulator.registerEvent(time, self._taskGenerator.id)
    
    def taskNodeId(self) -> int:
        return self._id
    
    def taskArrival(self, task: Task) -> None:
        #TODO
        pass
    
    