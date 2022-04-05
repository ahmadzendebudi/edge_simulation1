
from abc import abstractmethod
from typing import Any, Sequence
from simulator.core.process import Process
from simulator.core.task import Task
from simulator.core.task_queue import TaskQueue
import numpy as np

class TaskMultiplexerPlug:
    @abstractmethod
    def fetchState(self, task: Task, processId: int) -> Sequence[float]:
        '''It should not add the workload of the task to any queues, this does not include the edition of
        the task to the edge queue for approximation'''
        pass
    
    @abstractmethod
    def fetchTaskInflatedState(self, task: Task, processId: int) -> Sequence[float]:
        '''It should add the workload of the task to both local and edge queues, as if every 
        queue is required to process the task'''
        pass
    
    @abstractmethod
    def fetchMultiplexerQueue(self, processId: int) -> TaskQueue:
        pass
    
    @abstractmethod
    def taskLocalExecution(self, task: Task, processId: int) -> None:
        pass
    
    @abstractmethod
    def taskTransimission(self, task: Task, processId: int, destinationId: int) -> None:
        pass
    
    @abstractmethod
    def taskTransitionRecord(self, task: Task, state1, state2, actionObject) -> None:
        pass
    
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
        selection = None
        state1 = self._plug.fetchTaskInflatedState(task, self.id())
        if task.hopLimit() > 0:
            actionObject = self._selector.action(task, state1)
            selection = self._selector.select(actionObject)
        if selection == None:
            self._plug.taskLocalExecution(task, self.id())
        else:
            task.setHopLimit(task.hopLimit() - 1)
            self._plug.taskTransimission(task, self.id(), selection)
        state2 = self._plug.fetchState(task, self.id())
        self._plug.taskTransitionRecord(task, state1, state2, actionObject)