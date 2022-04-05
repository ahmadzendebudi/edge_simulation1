from abc import abstractmethod
from typing import Sequence

import numpy as np
from tf_agents import trajectories as tj
from tf_agents import specs

from simulator.config import Config


class Transition:
    def __init__(self, taskId, state1 = None, state2 = None, action = None, delay = None, completed = False) -> None:
        self.taskId = taskId
        self.state1 = state1
        self.state2 = state2
        self.action = action
        self.delay = delay
        self.completed = completed
    
    def reward(self):
        #TODO compute reward properly
        #TODO introduce a deadline penalty: it should be implemented either here or in DRL code
        return - self.delay
 
class TransitionUtil:
    @classmethod
    def convertToTfTransition(cls, transition: Transition):  
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
    
    @classmethod
    def convertStateToTfTimeStep(cls, state: Sequence[float]):
        if not hasattr(cls, 'discountnp'):
            cls.discount = Config.get("dql_learning_discount")
            cls.discountnp = np.array(cls.discount, np.float32)
            
        stepType = tj.time_step.StepType.MID
        observation = np.array(state, dtype=np.float32)
        
        return tj.time_step.TimeStep(step_type=stepType, observation=observation, reward= 0, discount=cls.discount)   

    @classmethod
    def tfObservationSpec(cls):
        return specs.array_spec.BoundedArraySpec((6,), np.float32, minimum=0, name='observation')
    
class TransitionRecorderPlug:
    @abstractmethod
    def transitionRecorderLimitReached(self, completedTransitions: Sequence[Transition]):
        pass
    
class TransitionRecorder:
    def __init__(self, plug: TransitionRecorderPlug) -> None:
        self._plug = plug
        
    @abstractmethod
    def put(self, transition: Transition):
        pass
    
    @abstractmethod
    def get(self, taskId: int):
        pass
    
    @abstractmethod
    def popCompleted(self) -> Sequence[Transition]:
        '''This function should clear all the completed transitions'''
        pass

class TwoStepTransitionRecorder(TransitionRecorder):
    def __init__(self, plug: TransitionRecorderPlug, completedTransitionLimit: int) -> None:
        self._transitionMap = {}
        self._completedTransitionCount = 0
        self._completedTransitionLimit = completedTransitionLimit
        super().__init__(plug)
    
    def put(self, transition: Transition):
        if transition.taskId in self._transitionMap:
            raise RuntimeError("A transition with the same task id already exists")
        self._transitionMap[transition.taskId] = transition

    def completeTransition(self, taskId: int, delay: float):
        transition = self._transitionMap[taskId]
        transition.delay = delay 
        transition.completed = True
        self._completedTransitionCount += 1
        if (self._completedTransitionCount >= self._completedTransitionLimit):
            self._plug.transitionRecorderLimitReached(self.popCompleted())
        
    def get(self, taskId: int):
        return self._transitionMap[taskId]
    
    def popCompleted(self) -> Sequence[Transition]:
        newtransitionMap = {}
        completedTransitionList = []
        for transition in self._transitionMap.values():
            if (transition.completed):
                completedTransitionList.append(transition)
            else:
                newtransitionMap[transition.taskId] = transition
        self._transitionMap = newtransitionMap
        return completedTransitionList