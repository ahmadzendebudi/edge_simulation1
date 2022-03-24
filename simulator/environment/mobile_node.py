from simulator.core import Node
from simulator.core import Connection

class MobileNode(Node):
    def __init__(self, id, edgeConnection: Connection) -> None:
        self._edgeConnection = edgeConnection
        super(MobileNode, self).__init__(id)
    
    def edgeConnection(self) -> Connection:
        self._edgeConnection