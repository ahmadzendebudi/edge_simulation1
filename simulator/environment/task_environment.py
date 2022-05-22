from typing import Any, Callable, Collection,  Tuple

from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.environment.edge_node import EdgeNode
from simulator.environment.mobile_node import MobileNode
from simulator.core.environment import Environment
from simulator.task_multiplexing.selector import TaskMultiplexerSelector
from simulator.task_multiplexing.transition_recorder import Transition, TwoStepTransitionRecorder
   
class TaskEnvironment(Environment):
    def __init__(self, edgeNodes: dict[int, EdgeNode], mobileNodes: dict[int, MobileNode], 
                 edgeSelectorGenerator: Callable[[Tuple[Any]], TaskMultiplexerSelector],
                 mobileSelectorGenerator: Callable[[Tuple[Any]], TaskMultiplexerSelector],
                 edgeRewardFunction: Callable[[Transition], float] = None,
                 mobileRewardFunction: Callable[[Transition], float] = None) -> None:
        self._edgeNodes = edgeNodes
        self._mobileNodes = mobileNodes
        self._edgeRewardFunction = edgeRewardFunction
        self._mobileRewardFunction = mobileRewardFunction
        self._moblie_multiplex_selector = mobileSelectorGenerator(MobileNode.fetchStateShape())
        self._edge_multiplex_selector = edgeSelectorGenerator(EdgeNode.fetchStateShape())
    
    def initialize(self, simulator: Simulator, 
                   mobileTransitionWatchers: Collection[Callable[[Transition], Any]] = [],
                   edgeTransitionWatchers: Collection[Callable[[Transition], Any]] = []) -> None:
        self._simulator = simulator
        for node in self._edgeNodes + self._mobileNodes:
            simulator.registerNode(node)
        
        for edgeNode in self._edgeNodes:
            edgeNode.initializeConnection(simulator)
        for mobileNode in self._mobileNodes:
            mobileNode.initializeConnection(simulator)
        
        for mobileNode in self._mobileNodes:
            mobileNode.setTransitionRecorder(TwoStepTransitionRecorder(mobileTransitionWatchers))
            mobileNode.setRewardFunction(self._mobileRewardFunction)
        
        for edgeNode in self._edgeNodes:
            edgeNode.setTransitionRecorder(TwoStepTransitionRecorder(edgeTransitionWatchers))
            edgeNode.setRewardFunction(self._edgeRewardFunction)
            
        for edgeNode in self._edgeNodes:
            edgeNode.initializeProcesses(simulator, self._edge_multiplex_selector)
        for mobileNode in self._mobileNodes:
            mobileNode.initializeProcesses(simulator, self._moblie_multiplex_selector)
        
    
    def edgeNode(self, id: int) -> EdgeNode:
        return self._edgeNodes[id]
    
    def mobileNode(self, id: int) -> MobileNode:
        return self._mobileNodes[id]