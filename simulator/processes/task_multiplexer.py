
from abc import abstractmethod
from simulator.core.process import Process
from simulator.core.task import Task
from simulator.core.task_queue import TaskQueue
import numpy as np

class TaskMultiplexerPlug:
    @abstractmethod
    def fetchMultiplexerQueue(self) -> TaskQueue:
        pass
    
    @abstractmethod
    def taskLocalExecution(self, task: Task) -> None:
        pass
    
    @abstractmethod
    def taskTransimission(self, task: Task) -> None:
        pass
    
class TaskMultiplexer(Process):
    
    def __init__(self, plug: TaskMultiplexerPlug) -> None:
        super().__init__()
        self._plug = plug
        
    def wake(self) -> None:
        queue = self._plug.fetchMultiplexerQueue()
        if queue.qsize != 0:
            self._multiplex(queue.get())
        return super().wake()
    
    def _multiplex(self, task: Task) -> None:
        #TODO this requires a lot of attention, for now it's just random
        #TODO it should be somehow plugable, instead of the multiplexer itself deciding the strategy
        if (np.random.randint(0, 1) == 1):
            self._plug.taskLocalExecution(task)
        else:
            self._plug.taskTransimission(task)
        