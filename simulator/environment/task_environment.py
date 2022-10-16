from typing import Any, Callable, Collection,  Tuple

from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.core.task import Task
from simulator.environment.edge_node import EdgeNode
from simulator.environment.mobile_node import MobileNode
from simulator.core.environment import Environment
from simulator.task_multiplexing.selector import MultiplexerSelectorBehaviour, TaskMultiplexerSelector
from simulator.task_multiplexing.transition_recorder import Transition, TwoStepTransitionRecorder
   
class TaskEnvironment(Environment):
    def __init__(self, edgeNodes: dict[int, EdgeNode], mobileNodes: dict[int, MobileNode], 
                 edgeSelectorGenerator: Callable[[Tuple[Any], Callable[[Transition], float]], TaskMultiplexerSelector],
                 mobileSelectorGenerator: Callable[[Tuple[Any], Callable[[Transition], float]], TaskMultiplexerSelector],
                 edgeRewardFunction: Callable[[Transition], float] = None,
                 mobileRewardFunction: Callable[[Transition], float] = None) -> None:
        self._edgeNodes = edgeNodes
        self._mobileNodes = mobileNodes
        self._edgeRewardFunction = edgeRewardFunction
        self._mobileRewardFunction = mobileRewardFunction
        self._mobileSelectorGenerator = mobileSelectorGenerator
        self._edgeSelectorGenerator = edgeSelectorGenerator
    
    def initialize(self, simulator: Simulator, 
                   mobileTransitionWatchers: Collection[Callable[[Transition], Any]] = None,
                   edgeTransitionWatchers: Collection[Callable[[Transition], Any]] = None,
                   mobileUtilizationWatchers: Collection[Callable[[Task, float, float], Any]] = None,
                   edgeUtilizationWatchers: Collection[Callable[[Task, float, float], Any]] = None) -> None:
        if mobileTransitionWatchers == None:
            mobileTransitionWatchers = []
        if edgeTransitionWatchers == None:
            edgeTransitionWatchers = []
        if mobileUtilizationWatchers == None:
            mobileUtilizationWatchers = []
        if edgeUtilizationWatchers == None:
            edgeUtilizationWatchers = []

        self._simulator = simulator
        for node in self._edgeNodes + self._mobileNodes:
            simulator.registerNode(node)
        
        for edgeNode in self._edgeNodes:
            edgeNode.initializeConnection(simulator)
        for mobileNode in self._mobileNodes:
            mobileNode.initializeConnection(simulator)
        
        
        edge_multiplex_selector = self._edgeSelectorGenerator(EdgeNode.fetchStateShape(), self._edgeRewardFunction)
        moblie_multiplex_selector = self._mobileSelectorGenerator(MobileNode.fetchStateShape(), self._mobileRewardFunction)

        for edgeNode in self._edgeNodes:
            edgeNode.setTransitionRecorder(TwoStepTransitionRecorder(edgeTransitionWatchers))

            edge_selector = edge_multiplex_selector
            mobile_selector = None

            if moblie_multiplex_selector.behaviour().trainMethod == MultiplexerSelectorBehaviour.TRAIN_REMOTE:
                mobile_selector = self._mobileSelectorGenerator(MobileNode.fetchStateShape(), self._mobileRewardFunction)
            if edge_multiplex_selector.behaviour().trainMethod != MultiplexerSelectorBehaviour.TRAIN_SHARED:
                edge_selector = self._edgeSelectorGenerator(EdgeNode.fetchStateShape(), self._edgeRewardFunction)
            
            edgeNode.initializeProcesses(simulator, edge_selector, edgeUtilizationWatchers, mobile_selector)
            

        
        for mobileNode in self._mobileNodes:
            mobileNode.setTransitionRecorder(TwoStepTransitionRecorder(mobileTransitionWatchers))
            
            mobile_selector = moblie_multiplex_selector

            if moblie_multiplex_selector.behaviour().trainMethod != MultiplexerSelectorBehaviour.TRAIN_SHARED:
                mobile_selector = self._mobileSelectorGenerator(MobileNode.fetchStateShape(), self._mobileRewardFunction)
            
            mobileNode.initializeProcesses(simulator, mobile_selector, mobileUtilizationWatchers)
        
    
    def edgeNode(self, id: int) -> EdgeNode:
        return self._edgeNodes[id]
    
    def mobileNode(self, id: int) -> MobileNode:
        return self._mobileNodes[id]