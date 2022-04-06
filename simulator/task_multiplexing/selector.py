from abc import abstractmethod
from typing import Any, Sequence

import numpy as np
from simulator.core import Task

class TaskMultiplexerSelector:    
    
    @abstractmethod
    def action(self, task: Task, state: Sequence[float]) -> Any:
        '''First the actionObject is returned through this function. action object is used
        for recording the transition. the action object is then passed on to select function
        to retrieve the selection'''
        pass
    
    @abstractmethod
    def select(self, action: Any) -> int:
        '''it should return None for local execution, otherwise the id of the destination node'''
        pass
    

class TaskMultiplexerSelectorRandom(TaskMultiplexerSelector):
    def __init__(self, destIds: Sequence[int]) -> None:
        self._destIds = destIds + [None]
            
    def action(self, task: Task, state: Sequence[float]) -> Any:
        return np.random.choice(self._destIds)
    
    def select(self, action: Any) -> int:
        return action
    
class TaskMultiplexerSelectorLocal(TaskMultiplexerSelector):
    def action(self, task: Task, state: Sequence[float]) -> int:
        return None
    
    def select(self, action: Any) -> int:
        return action
            
   