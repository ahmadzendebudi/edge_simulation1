from abc import abstractmethod
from importlib.abc import Traversable
from typing import Sequence


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
    

class TransitionRecorder:
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
    
class TwoStepTransitionRecorderPlug:
    @abstractmethod
    def transitionRecorderLimitReached(self, completedTransitions: Sequence[Transition]):
        pass
    
class TwoStepTransitionRecorder(TransitionRecorder):
    def __init__(self, plug: TwoStepTransitionRecorderPlug, completedTransitionLimit: int) -> None:
        self._transitionMap = {}
        self._plug = plug
        self._completedTransitionCount = 0
        self._completedTransitionLimit = completedTransitionLimit
    
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