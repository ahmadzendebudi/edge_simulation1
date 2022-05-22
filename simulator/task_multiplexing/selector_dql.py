from abc import abstractmethod
from typing import Any, Sequence, Tuple
from simulator.core.task import Task
from simulator.dql.transition_agent import TransitionAgent
from simulator.processes.task_multiplexer import TaskMultiplexerSelector
from simulator import Config
from simulator import Logger

import tensorflow as tf
from tf_agents import agents
from tf_agents import trajectories as tj
from tf_agents.typing import types
from tf_agents import networks
from tf_agents.networks import network
from tf_agents import utils
from tf_agents import specs
from tf_agents import policies
import numpy as np

from simulator.task_multiplexing.transition import Transition

class TaskMultiplexerSelectorDql(TaskMultiplexerSelector):
    
    def __init__(self, stateShape: Tuple[int], bufferSize: int = 10000, trainInterval: int = 100) -> None:
        observation_spec = specs.array_spec.BoundedArraySpec(stateShape, np.float32, minimum=0, name='observation')
        action_spec = specs.array_spec.BoundedArraySpec((), np.int32, 0, 1, 'action')
        self._transitionAgent = TransitionAgent(observation_spec, action_spec, bufferSize)
        self._trainInterval = trainInterval
        self._trainIntervalCounter = 0
        super().__init__()
    
    def action(self, task: Task, state: Sequence[float]) -> tj.PolicyStep:
        timeStep = TaskMultiplexerSelectorDql._convertStateToTfTimeStep(state)
        return self._transitionAgent.action(timeStep)
    
    def select(self, actionStep) -> int:
        '''it will return none for local and 1 for remote execution'''
        action = actionStep.action
        if action == 0:
            return None
        else:
            return action
    
    def addToBuffer(self, transition: Transition):
        tfTransition = TaskMultiplexerSelectorDql._convertToTfTransition(transition)
        self._transitionAgent.addToBuffer(tfTransition)
        self._trainIntervalCounter += 1
        if (self._trainIntervalCounter >= self._trainInterval):
            self._trainIntervalCounter = 0
            self._train()
        Logger.log("addToBuffer, transition:" + str(transition), 2)
            
    def _train(self) -> None:
        self._transitionAgent.train()
           
    @classmethod
    def _convertStateToTfTimeStep(cls, state: Sequence[float]):
        if not hasattr(cls, 'discountnp'):
            cls.discount = Config.get("dql_learning_discount")
            cls.discountnp = np.array(cls.discount, np.float32)
            
        stepType = tj.time_step.StepType.MID
        observation = np.array(state, dtype=np.float32)
        
        return tj.time_step.TimeStep(step_type=stepType, observation=observation, reward= 0, discount=cls.discount) 
    
    @classmethod
    def _convertToTfTransition(cls, transition: Transition):  
        #Store current completed transitions to transition buffer
        if not hasattr(cls, 'discountnp'):
            cls.discount = Config.get("dql_learning_discount")
            cls.discountnp = np.array(cls.discount, np.float32)
        
        observation1 = np.array(transition.state1, dtype=np.float32)
        observation2 = np.array(transition.state2, dtype=np.float32)
        reward = np.array(transition.reward(), np.float32)
        stepType = tj.time_step.StepType.MID
        time_step1 = tj.time_step.TimeStep(step_type=stepType, reward=reward, 
                                            observation=observation1, discount=cls.discountnp)
        time_step2 = tj.time_step.TimeStep(step_type=stepType, reward=reward, 
                                            observation=observation2, discount=cls.discountnp)
        action_step = transition.action
        return tj.Transition(time_step1, action_step, time_step2)
    