from abc import abstractmethod
from typing import Any, Callable, Collection, Sequence

from simulator.task_multiplexing.transition import Transition

  
class TransitionRecorder:
    def __init__(self) -> None:
        pass
        
    @abstractmethod
    def put(self, transition: Transition):
        pass
    
    @abstractmethod
    def get(self, taskId: int):
        pass
    
    @abstractmethod
    def completeTransition(self, taskId: int, delay: float, powerConsumed: float) -> Transition:
        pass
    

class TwoStepTransitionRecorder(TransitionRecorder):
    def __init__(self, transitionWatchers: Collection[Callable[[Transition], Any]] = []) -> None:
        self._transitionMap = {}
        self._transitionWatchers = transitionWatchers
        super().__init__()
    
    def put(self, transition: Transition):
        if transition.taskId in self._transitionMap:
            raise RuntimeError("A transition with the same task id already exists")
        self._transitionMap[transition.taskId] = transition

    def completeTransition(self, taskId: int, delay: float, powerConsumed: float) -> Transition:
        transition = self._transitionMap[taskId]
        transition.delay = delay
        transition.powerConsumed = powerConsumed
        transition.completed = True
        
        for transitionWatcher in self._transitionWatchers:
            transitionWatcher(transition)
        
        return self._transitionMap.pop(taskId)
        
    def get(self, taskId: int):
        return self._transitionMap[taskId]
    