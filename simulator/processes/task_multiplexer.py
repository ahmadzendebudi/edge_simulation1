
from abc import abstractmethod
from typing import Sequence
from simulator.core.process import Process
from simulator.core.task import Task
from simulator.core.task_queue import TaskQueue
import numpy as np

class TaskMultiplexerPlug:
    @abstractmethod
    def fetchMultiplexerQueue(self, processId: int) -> TaskQueue:
        pass
    
    @abstractmethod
    def taskLocalExecution(self, task: Task, processId: int) -> None:
        pass
    
    @abstractmethod
    def taskTransimission(self, task: Task, processId: int, destinationId: int) -> None:
        pass
    
class TaskMultiplexerSelector:    
    @abstractmethod
    def select(self, task: Task) -> int:
        '''it should return None for local execution, otherwise the id of the destination node'''
        pass

class TaskMultiplexerSelectorRandom(TaskMultiplexerSelector):
    def __init__(self, destIds: Sequence[int]) -> None:
        self._destIds = destIds + [None]
            
    def select(self, task: Task) -> int:
        return np.random.choice(self._destIds)
    
class TaskMultiplexerSelectorLocal(TaskMultiplexerSelector):
    def select(self, task: Task) -> int:
        return None
            
   
class TaskMultiplexer(Process):
    
    def __init__(self, plug: TaskMultiplexerPlug, selector: TaskMultiplexerSelector) -> None:
        super().__init__()
        self._plug = plug
        self._selector = selector
        
    def wake(self) -> None:
        queue = self._plug.fetchMultiplexerQueue(self._id)
        if queue.qsize() != 0:
            self._multiplex(queue.get())
        return super().wake()
    
    def _multiplex(self, task: Task) -> None:
        selection = self._selector.select(task)
        if selection == None:
            self._plug.taskLocalExecution(task, self.id())
        else:
            self._plug.taskTransimission(task, self.id(), selection)
        