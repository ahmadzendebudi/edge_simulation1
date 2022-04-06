from abc import abstractmethod
from typing import Sequence, Tuple

from simulator.core.task import Task


class StateHandler:
    @abstractmethod
    def fetchState(self, task: Task) -> Sequence[float]:
        '''It should not add the workload of the task to any queues, this does not include the edition of
        the task to the edge queue for approximation'''
        pass
    
    @abstractmethod
    def fetchTaskInflatedState(self, task: Task) -> Sequence[float]:
        '''It should add the workload of the task to both local and edge queues, as if every 
        queue is required to process the task'''
        pass
    
    @abstractmethod
    def recordTransition(self, task: Task, state1, state2, actionObject) -> None:
        pass
    
    @classmethod
    def fetchStateShape(cls) -> Tuple[int]:
        '''It should return the shape of states similar to numpy shapes'''
        raise NotImplementedError("Subclasses must implement this method")