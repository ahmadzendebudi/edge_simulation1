from typing import Sequence
from simulator import core
from simulator import environment as env

class EdgeNode(core.Node):
    def __init__(self, id: int, edgeConnections: Sequence[core.Connection],
                 mobileDeviceConnections: Sequence[core.Connection]) -> None:
        self._edgeConnections = edgeConnections
        self._mobileDeviceConnections = mobileDeviceConnections
        super().__init__(id)
    
    def edgeConnections(self) -> Sequence[core.Connection]:
        self._edgeConnections
    
    def mobileDeviceConnections(self) -> Sequence[core.Connection]:
        self._mobileDeviceConnections
        
    def setup(self, env: env.TaskEnvironment):
        self._env = env
        self._localQueue = core.TaskQueue()
        self._TransmitQueue = core.TaskQueue()
        self._multiplexQueue = core.TaskQueue()
        