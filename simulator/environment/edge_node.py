from typing import Sequence
from simulator.core import Node
from simulator.core import Connection

class EdgeNode(Node):
    def __init__(self, id: int, edgeConnections: Sequence[Connection],
                 mobileDeviceConnections: Sequence[Connection]) -> None:
        self._edgeConnections = edgeConnections
        self._mobileDeviceConnections = mobileDeviceConnections
        super(EdgeNode, self).__init__(id)
    
    def edgeConnections(self) -> Sequence[Connection]:
        self._edgeConnections
    
    def mobileDeviceConnections(self) -> Sequence[Connection]:
        self._mobileDeviceConnections