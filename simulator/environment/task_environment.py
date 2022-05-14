from typing import Any, Callable, Collection, Sequence, Tuple

import numpy as np
from simulator.common import Common
from simulator.config import Config
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.core.task import Task
from simulator.environment.edge_node import EdgeNode
from simulator.environment.mobile_node import MobileNode
from simulator.core.environment import Environment
from simulator.logger import Logger
from simulator.task_multiplexing.selector import TaskMultiplexerSelector, TaskMultiplexerSelectorLocal, TaskMultiplexerSelectorRandom
from simulator.task_multiplexing.transition_recorder import Transition, TransitionRecorderPlug, TwoStepTransitionRecorder

from tf_agents import specs

from simulator.task_multiplexing.selector_dql import TaskMultiplexerSelectorDql
   
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
        
        #self._moblie_multiplex_dql_selector = TaskMultiplexerSelectorDql(
        #    MobileNode.fetchStateShape(), Config.get("dql_training_buffer_size"))
        
        #self._edge_multiplex_dql_selector = TaskMultiplexerSelectorDql(
        #    EdgeNode.fetchStateShape(), Config.get("dql_training_buffer_size"))
        
        for edgeNode in self._edgeNodes:
            edgeNode.initializeProcesses(simulator, self._edge_multiplex_selector)
        for mobileNode in self._mobileNodes:
            mobileNode.initializeProcesses(simulator, self._moblie_multiplex_selector)
        
        self._mobileTaskSelectorProcess = Process()
        self._mobileTaskSelectorProcess.wake = self._trainMobileTaskSelector
        self._simulator.registerProcess(self._mobileTaskSelectorProcess)
        
        #TODO For now, all nodes magically share transition history
        transitionPlug = TransitionRecorderPlug()
        transitionPlug.transitionRecorderLimitReached = self._mobileTransitionRecorderLimitReached
        transitionRecorder = TwoStepTransitionRecorder(transitionPlug, Config.get("dql_training_interval"),
                                                       mobileTransitionWatchers)
        for mobileNode in self._mobileNodes:
            mobileNode.setTransitionRecorder(transitionRecorder)
            mobileNode.setRewardFunction(self._mobileRewardFunction)
            
        self._edgeTaskSelectorProcess = Process()
        self._edgeTaskSelectorProcess.wake = self._trainEdgeTaskSelector
        self._simulator.registerProcess(self._edgeTaskSelectorProcess)
        
        #TODO For now, all nodes magically share transition history
        transitionPlug = TransitionRecorderPlug()
        transitionPlug.transitionRecorderLimitReached = self._edgeTransitionRecorderLimitReached
        transitionRecorder = TwoStepTransitionRecorder(transitionPlug, Config.get("dql_training_interval"),
                                                       edgeTransitionWatchers)
        for edgeNode in self._edgeNodes:
            edgeNode.setTransitionRecorder(transitionRecorder)
            edgeNode.setRewardFunction(self._edgeRewardFunction)
    
    def _mobileTransitionRecorderLimitReached(self, completedTransitions: Sequence[Transition]):
        self._mobileCompletedTransitionList = completedTransitions
        self._simulator.registerEvent(Common.time(), self._mobileTaskSelectorProcess.id())
    
    def _edgeTransitionRecorderLimitReached(self, completedTransitions: Sequence[Transition]):
        self._edgeCompletedTransitionList = completedTransitions
        self._simulator.registerEvent(Common.time(), self._edgeTaskSelectorProcess.id())
        
    def _observationSpec(self):
        return specs.array_spec.BoundedArraySpec((6,), np.float32, minimum=0, name='observation')
    
    def _trainMobileTaskSelector(self):
        #Add to buffer
        for transition in self._mobileCompletedTransitionList:
            self._moblie_multiplex_selector.addToBuffer(transition)
        
        #Train
        self._moblie_multiplex_selector.train()
    
    def _trainEdgeTaskSelector(self):
        #Add to buffer
        for transition in self._edgeCompletedTransitionList:
            self._edge_multiplex_selector.addToBuffer(transition)
            Logger.log("add to edge transition buffer: " + str(transition), 3)
        
        #Train
        self._edge_multiplex_selector.train()
        
    def edgeNode(self, id: int) -> EdgeNode:
        return self._edgeNodes[id]
    
    def mobileNode(self, id: int) -> MobileNode:
        return self._mobileNodes[id]