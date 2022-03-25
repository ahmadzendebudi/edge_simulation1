from simulator.core.node import Node
from simulator.core.connection import Connection
from simulator.core.process import ProcessPlug
from simulator.core.task_queue import TaskQueue, TaskQueuePlug
from simulator.processes.mobile import TaskGeneratorPlug
from simulator.processes.mobile.task_generator import TaskGenerator

class MobileNode(Node, TaskGeneratorPlug):
    def __init__(self, id, edgeConnection: Connection) -> None:
        self._edgeConnection = edgeConnection
        super().__init__(id)
    
    def edgeConnection(self) -> Connection:
        self._edgeConnection
    
    def setup(self, processPlug: ProcessPlug, taskQueuePlug: TaskQueuePlug):
        self._localQueue = TaskQueue(taskQueuePlug)
        self._TransmitQueue = TaskQueue(taskQueuePlug)
        self._multiplexQueue = TaskQueue(taskQueuePlug)
        self._taskGenerator = TaskGenerator(processPlug, self)
    
    def registerTask(self, time: int):
        pass
    
    