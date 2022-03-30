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

class ListTransitionRecorder(TransitionRecorder):
    def __init__(self) -> None:
        self._transitionMap = {}
    
    def put(self, transition: Transition):
        if transition.taskId in self._transitionMap:
            raise RuntimeError("A transition with the same task id already exists")
        self._transitionMap[transition.taskId] = transition

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