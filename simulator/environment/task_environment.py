
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
from simulator.environment.transition_recorder import Transition, TwoStepTransitionRecorder, TwoStepTransitionRecorderPlug

from tf_agents import trajectories as tj
from tf_agents import specs

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
        
        for edgeNode in self._edgeNodes:
            edgeNode.initializeProcesses(simulator)
        for mobileNode in self._mobileNodes:
            mobileNode.initializeProcesses(simulator, self._moblie_multiplex_dql_selector)
        
        self._taskSelectorProcess = Process()
        self._taskSelectorProcess.wake = self._trainTaskSelector
        self._simulator.registerProcess(self._taskSelectorProcess)
        
        #TODO For now, all nodes magically share transition history
        transitionPlug = TwoStepTransitionRecorderPlug()
        transitionPlug.transitionRecorderLimitReached = self._mobileTransitionRecorderLimitReached
        transitionRecorder = TwoStepTransitionRecorder(transitionPlug, Config.get("dql_training_interval"))
        for mobileNode in self._mobileNodes:
            mobileNode.setTransitionRecorder(transitionRecorder)
    
    def _mobileTransitionRecorderLimitReached(self, completedTransitions: Sequence[Transition]):
        self._mobileCompletedTransitionList = completedTransitions
        self._simulator.registerEvent(Common.time(), self._taskSelectorProcess.id())
    
    
    def _observationSpec(self):
        return specs.array_spec.BoundedArraySpec((5,), np.float32, minimum=0, name='observation')
    
    def _trainTaskSelector(self):
        #Store current completed transitions to transition buffer
        discount = Config.get("dql_learning_discount")
        discount = np.array(discount, np.float32)
        for transition in self._mobileCompletedTransitionList:
            observation1 = np.array(transition.state1, dtype=np.float32)
            observation2 = np.array(transition.state2, dtype=np.float32)
            reward = np.array(transition.reward(), np.float32)
            stepType = tj.time_step.StepType.MID
            time_step1 = tj.time_step.TimeStep(step_type=stepType, reward=reward, 
                                               observation=observation1, discount=discount)
            time_step2 = tj.time_step.TimeStep(step_type=stepType, reward=reward, 
                                               observation=observation2, discount=discount)
            action_step = transition.action
            self._moblie_multiplex_dql_selector.addToBuffer(tj.Transition(time_step1, action_step, time_step2))
        
        #Train
        self._moblie_multiplex_dql_selector.train()
    
     
    def mobileConvertStateToTimeStep(self, task: Task, state: Sequence[float]):
        stepType = tj.time_step.StepType.MID
        discount = Config.get("dql_learning_discount")
        observation = np.array(state, dtype=np.float32)
        
        return tj.time_step.TimeStep(step_type=stepType, observation=observation, reward= 0, discount=discount)
           
    def edgeNode(self, id: int) -> EdgeNode:
        return self._edgeNodes[id]
    
    def mobileNode(self, id: int) -> MobileNode:
        return self._mobileNodes[id]