
from simulator.core.simulator import Simulator
from simulator.environment.edge_node import EdgeNode
from simulator.environment.mobile_node import MobileNode
from simulator.core.environment import Environment
from simulator.environment.transition_recorder import ListTransitionRecorder

class TaskEnvironment(Environment):
    def __init__(self, edgeNodes: dict[int, EdgeNode], mobileNodes: dict[int, MobileNode]) -> None:
        self._edgeNodes = edgeNodes
        self._mobileNodes = mobileNodes
    
    def initialize(self, simulator: Simulator) -> None:
        
        for node in self._edgeNodes + self._mobileNodes:
            simulator.registerNode(node)
        
        for edgeNode in self._edgeNodes:
            edgeNode.initializeConnection(simulator)
        for mobileNode in self._mobileNodes:
            mobileNode.initializeConnection(simulator)
        
        for edgeNode in self._edgeNodes:
            edgeNode.initializeProcesses(simulator)
        for mobileNode in self._mobileNodes:
            mobileNode.initializeProcesses(simulator)

        #TODO For now, all nodes magically share transition history
        transitionRecorder = ListTransitionRecorder()
        for mobileNode in self._mobileNodes:
            mobileNode.setTransitionRecorder(transitionRecorder)
            
    def edgeNode(self, id: int) -> EdgeNode:
        return self._edgeNodes[id]
    
    def mobileNode(self, id: int) -> MobileNode:
        return self._mobileNodes[id]