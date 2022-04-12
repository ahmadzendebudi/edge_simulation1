from typing import Sequence

import numpy as np
from simulator.common import Common
from simulator.config import Config
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.environment.edge_node import EdgeNode
from simulator.environment.mobile_node import MobileNode
from simulator.core.environment import Environment
from simulator.task_multiplexing.selector import TaskMultiplexerSelectorLocal, TaskMultiplexerSelectorRandom
from simulator.task_multiplexing.transition_recorder import Transition, TransitionRecorderPlug, TwoStepTransitionRecorder

from tf_agents import specs

from simulator.task_multiplexing.selector_dql import TaskMultiplexerSelectorDql
   
class TaskEnvironment(Environment):
    def __init__(self, edgeNodes: dict[int, EdgeNode], mobileNodes: dict[int, MobileNode]) -> None:
        self._edgeNodes = edgeNodes
        self._mobileNodes = mobileNodes
    
    def initialize(self, simulator: Simulator) -> None:
        self._simulator = simulator
        for node in self._edgeNodes + self._mobileNodes:
            simulator.registerNode(node)
        
        for edgeNode in self._edgeNodes:
            edgeNode.initializeConnection(simulator)
        for mobileNode in self._mobileNodes:
            mobileNode.initializeConnection(simulator)
        
        
        self._moblie_multiplex_dql_selector = TaskMultiplexerSelectorDql(
            MobileNode.fetchStateShape(), Config.get("dql_training_buffer_size"))
        
        #TODO to be replaced
        self._edge_multiplex_dql_selector = TaskMultiplexerSelectorDql(
            EdgeNode.fetchStateShape(), Config.get("dql_training_buffer_size"))
        
        for edgeNode in self._edgeNodes:
            edgeNode.initializeProcesses(simulator, self._edge_multiplex_dql_selector)
        for mobileNode in self._mobileNodes:
            mobileNode.initializeProcesses(simulator, self._moblie_multiplex_dql_selector)
        
        self._mobileTaskSelectorProcess = Process()
        self._mobileTaskSelectorProcess.wake = self._trainMobileTaskSelector
        self._simulator.registerProcess(self._mobileTaskSelectorProcess)
        
        #TODO For now, all nodes magically share transition history
        transitionPlug = TransitionRecorderPlug()
        transitionPlug.transitionRecorderLimitReached = self._mobileTransitionRecorderLimitReached
        transitionRecorder = TwoStepTransitionRecorder(transitionPlug, Config.get("dql_training_interval"))
        for mobileNode in self._mobileNodes:
            mobileNode.setTransitionRecorder(transitionRecorder)
            
        self._edgeTaskSelectorProcess = Process()
        self._edgeTaskSelectorProcess.wake = self._trainEdgeTaskSelector
        self._simulator.registerProcess(self._edgeTaskSelectorProcess)
        
        #TODO For now, all nodes magically share transition history
        transitionPlug = TransitionRecorderPlug()
        transitionPlug.transitionRecorderLimitReached = self._edgeTransitionRecorderLimitReached
        transitionRecorder = TwoStepTransitionRecorder(transitionPlug, Config.get("dql_training_interval"))
        for edgeNode in self._edgeNodes:
            edgeNode.setTransitionRecorder(transitionRecorder)
    
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
            self._moblie_multiplex_dql_selector.addToBuffer(transition)
        
        #Train
        self._moblie_multiplex_dql_selector.train()
    
    def _trainEdgeTaskSelector(self):
        #Add to buffer
        for transition in self._edgeCompletedTransitionList:
            self._edge_multiplex_dql_selector.addToBuffer(transition)
        
        #Train
        self._edge_multiplex_dql_selector.train()
        
    def edgeNode(self, id: int) -> EdgeNode:
        return self._edgeNodes[id]
    
    def mobileNode(self, id: int) -> MobileNode:
        return self._mobileNodes[id]