from abc import abstractmethod
from typing import Any, Sequence

import numpy as np
from simulator.core import Task
from simulator.task_multiplexing.transition import Transition

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
    
    def addToBuffer(self, transition: Transition) -> None:
        pass
    

class TaskMultiplexerSelectorRandom(TaskMultiplexerSelector):
    def __init__(self) -> None:
        pass
            
    def action(self, task: Task, state: Sequence[float]) -> Any:
        return np.random.randint(0, 2)
    
    def select(self, action: Any) -> int:
        return action
    
class TaskMultiplexerSelectorLocal(TaskMultiplexerSelector):
    def action(self, task: Task, state: Sequence[float]) -> int:
        return 0
    
    def select(self, action: Any) -> int:
        return action
    

class TaskMultiplexerSelectorRemote(TaskMultiplexerSelector):
    def action(self, task: Task, state: Sequence[float]) -> int:
        return 1
    
    def select(self, action: Any) -> int:
        return action
            
   