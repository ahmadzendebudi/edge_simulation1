
from abc import abstractmethod
from typing import Sequence

import numpy as np
from simulator.common import Common
from simulator.config import Config
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.core.task import Task
from simulator.environment.edge_node import EdgeNode
from simulator.environment.mobile_node import MobileNode
from simulator.core.environment import Environment
from simulator.environment.transition_recorder import Transition, TransitionRecorder, TransitionRecorderPlug, TransitionUtil, TwoStepTransitionRecorder

from tf_agents import trajectories as tj
from tf_agents import specs
from simulator.processes.task_multiplexer import TaskMultiplexerSelector, TaskMultiplexerSelectorRandom

from simulator.processes.task_multiplexer_selector_dql import TaskMultiplexerSelectorDql, TaskMultiplexerSelectorDqlPlug
   
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
        
        self._mobile_multiplex_dql_selector_plug = TaskMultiplexerSelectorDqlPlug()
        self._mobile_multiplex_dql_selector_plug.convertStateToTimeStep = self.mobileConvertStateToTimeStep
        self._moblie_multiplex_dql_selector = TaskMultiplexerSelectorDql(
            self._observationSpec(), self._mobile_multiplex_dql_selector_plug,
            Config.get("dql_training_buffer_size"))
        #taskSelectorRandom = TaskMultiplexerSelectorRandom([0])
        
        for edgeNode in self._edgeNodes:
            edgeNode.initializeProcesses(simulator)
        for mobileNode in self._mobileNodes:
            mobileNode.initializeProcesses(simulator, self._moblie_multiplex_dql_selector)
           # mobileNode.initializeProcesses(simulator, taskSelectorRandom)
        
        self._taskSelectorProcess = Process()
        self._taskSelectorProcess.wake = self._trainTaskSelector
        self._simulator.registerProcess(self._taskSelectorProcess)
        
        #TODO For now, all nodes magically share transition history
        transitionPlug = TransitionRecorderPlug()
        transitionPlug.transitionRecorderLimitReached = self._mobileTransitionRecorderLimitReached
        transitionRecorder = TwoStepTransitionRecorder(transitionPlug, Config.get("dql_training_interval"))
        for mobileNode in self._mobileNodes:
            mobileNode.setTransitionRecorder(transitionRecorder)
    
    def _mobileTransitionRecorderLimitReached(self, completedTransitions: Sequence[Transition]):
        self._mobileCompletedTransitionList = completedTransitions
        self._simulator.registerEvent(Common.time(), self._taskSelectorProcess.id())
    
    
    def _observationSpec(self):
        return specs.array_spec.BoundedArraySpec((6,), np.float32, minimum=0, name='observation')
    
    def _trainTaskSelector(self):
        #Add to buffer
        for transition in self._mobileCompletedTransitionList:
            self._moblie_multiplex_dql_selector.addToBuffer(TransitionUtil.convertToTfTransition(transition))
        
        #Train
        self._moblie_multiplex_dql_selector.train()
    
     
    def mobileConvertStateToTimeStep(self, task: Task, state: Sequence[float]):
        return TransitionUtil.convertStateToTimeStep(state)
           
    def edgeNode(self, id: int) -> EdgeNode:
        return self._edgeNodes[id]
    
    def mobileNode(self, id: int) -> MobileNode:
        return self._mobileNodes[id]