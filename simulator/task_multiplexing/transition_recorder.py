from abc import abstractmethod
from typing import Sequence

from simulator.task_multiplexing.transition import Transition


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