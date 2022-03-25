
from simulator.core.simulator import Simulator
from simulator.environment.edge_node import EdgeNode
from simulator.environment.mobile_node import MobileNode
from simulator.core.environment import Environment

class TaskEnvironment(Environment):
    def __init__(self, edgeNodes: dict[int, EdgeNode], mobileNodes: dict[int, MobileNode]) -> None:
        self._edgeNodes = edgeNodes
        self._mobileNodes = mobileNodes
    
    def setup(self, simulator: Simulator) -> None:
        for edgeNode in self._edgeNodes:
            edgeNode.setup(simulator)
        for mobileNode in self._mobileNodes:
            mobileNode.setup(simulator)
    
    def edgeNode(self, id: int) -> EdgeNode:
        return self._edgeNodes[id]
    
    def mobileNode(self, id: int) -> MobileNode:
        return self._mobileNodes[id]