
from abc import abstractmethod
from simulator.core.process import Process
from simulator.core.task import Task
from simulator.core.task_queue import TaskQueue

from simulator.task_multiplexing.selector import TaskMultiplexerSelector
from simulator.task_multiplexing.state_handler import StateHandler

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
    

class TaskMultiplexer(Process):
    
    def __init__(self, plug: TaskMultiplexerPlug, selector: TaskMultiplexerSelector, stateHandler: StateHandler) -> None:
        super().__init__()
        self._plug = plug
        self._selector = selector
        self._stateHandler = stateHandler
        
    def wake(self) -> None:
        queue = self._plug.fetchMultiplexerQueue(self._id)
        if queue.qsize() != 0:
            self._multiplex(queue.get())
        return super().wake()
    
    def _multiplex(self, task: Task) -> None:
        selection = None
        state1 = self._stateHandler.fetchTaskInflatedState(task, self.id())
        if task.hopLimit() > 0:
            actionObject = self._selector.action(task, state1)
            selection = self._selector.select(actionObject)
        if selection == None:
            self._plug.taskLocalExecution(task, self.id())
        else:
            task.setHopLimit(task.hopLimit() - 1)
            self._plug.taskTransimission(task, self.id(), selection)
        state2 = self._stateHandler.fetchState(task, self.id())
        self._stateHandler.recordTransition(task, state1, state2, actionObject)