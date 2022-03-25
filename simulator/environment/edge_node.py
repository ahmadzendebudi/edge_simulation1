from typing import Sequence
from simulator.core import Node
from simulator.core import Connection
from simulator.core import TaskQueue
from simulator.core.process import ProcessPlug
from simulator.core.task_queue import TaskQueuePlug

class EdgeNode(Node):
    def __init__(self, id: int, edgeConnections: Sequence[Connection],
                 mobileDeviceConnections: Sequence[Connection]) -> None:
        self._edgeConnections = edgeConnections
        self._mobileDeviceConnections = mobileDeviceConnections
        super().__init__(id)
    
    def edgeConnections(self) -> Sequence[Connection]:
        self._edgeConnections
    
    def mobileDeviceConnections(self) -> Sequence[Connection]:
        self._mobileDeviceConnections
        
    def setup(self, processPlug: ProcessPlug, taskQueuePlug: TaskQueuePlug):
        self._localQueue = TaskQueue(taskQueuePlug)
        self._TransmitQueue = TaskQueue(taskQueuePlug)
        self._multiplexQueue = TaskQueue(taskQueuePlug)
        