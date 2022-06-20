from abc import abstractmethod
from typing import Any, Callable, Sequence, Tuple

import numpy as np
from simulator.core import Task
from simulator.task_multiplexing.transition import Transition

class MultiplexerSelectorBehaviour:
    trainLocal = True
    trainRemote = False

class MultiplexerSelectorModel:
    @abstractmethod
    def model(self) -> Any:
        pass

    @abstractmethod
    def size(self) -> int:
        pass

class TaskMultiplexerSelector:    
    
    def __init__(self, rewardFunction: Callable[['Transition'], float],
                 behaviour: MultiplexerSelectorBehaviour = None) -> None:
        self._rewardFunction = rewardFunction
        if behaviour == None:
            self._behaviour = MultiplexerSelectorBehaviour()
        else:
            self._behaviour = behaviour

    def rewardFunction(self) -> Callable[['Transition'], float]:
        return self._rewardFunction
        
    def behaviour(self) -> MultiplexerSelectorBehaviour:
        return self._behaviour

    def addToBuffer(self, transition: Transition) -> None:
        self._addToBuffer(transition)


    @abstractmethod
    def action(self, task: Task, state: Sequence[float]) -> Tuple[Any, int]:
        '''The first element of tuple is the actionObject used for transition recording and the second element is the selection given to node'''
        pass
    
    @abstractmethod
    def _addToBuffer(self, transition: Transition) -> None:
        pass
    
    def extractModel(self) -> MultiplexerSelectorModel:
        pass

    def setModel(self, model: MultiplexerSelectorModel):
        pass


class TaskMultiplexerSelectorRandom(TaskMultiplexerSelector):
    def __init__(self, rewardFunction: Callable[[Transition], float]) -> None:
        super().__init__(rewardFunction)
            
    def action(self, task: Task, state: Sequence[float]) -> Tuple[Any, int]:
        action = np.random.randint(0, 2)
        return action, action
    
    def _addToBuffer(self, transition: Transition) -> None:
        pass
    
class TaskMultiplexerSelectorLocal(TaskMultiplexerSelector):
    def __init__(self, rewardFunction: Callable[[Transition], float]) -> None:
        super().__init__(rewardFunction)

    def action(self, task: Task, state: Sequence[float]) -> Tuple[Any, int]:
        action = 0
        return action, action

    def _addToBuffer(self, transition: Transition) -> None:
        pass
    

class TaskMultiplexerSelectorRemote(TaskMultiplexerSelector):
    def __init__(self, rewardFunction: Callable[[Transition], float]) -> None:
        super().__init__(rewardFunction)

    def action(self, task: Task, state: Sequence[float]) -> Tuple[Any, int]:
        action = 1
        return action, action
    
    def _addToBuffer(self, transition: Transition) -> None:
        pass
            
   