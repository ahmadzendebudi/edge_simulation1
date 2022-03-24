from simulator import core
from simulator import environment as env

class MobileNode(core.Node):
    def __init__(self, id, edgeConnection: core.Connection) -> None:
        self._edgeConnection = edgeConnection
        super().__init__(id)
    
    def edgeConnection(self) -> core.Connection:
        self._edgeConnection
    
    def setup(self, env: env.TaskEnvironment):
        self._env = env