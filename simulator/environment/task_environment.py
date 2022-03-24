from simulator import environment as env
from simulator import core

class TaskEnvironment(core.Environment):
    def __init__(self, edgeNodes: dict[int, env.EdgeNode], mobileNodes: dict[int, env.MobileNode]) -> None:
        self._edgeNodes = edgeNodes
        self._mobileNodes = mobileNodes
        for edgeNode in self._edgeNodes:
            edgeNode.setup(self)
        for mobileNode in self._mobileNodes:
            mobileNode.setup(self)
    
    def edgeNode(self, id: int) -> env.EdgeNode:
        return self._edgeNodes[id]
    
    def mobileNode(self, id: int) -> env.MobileNode:
        return self._mobileNodes[id]