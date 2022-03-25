
from abc import abstractmethod
from simulator.core.task import Task
from queue import Queue

class TaskQueuePlug:
    @abstractmethod
    def registerTaskQueue(self, taskQueue) -> int:
        pass

class TaskQueue:
    def __init__(self, plug: TaskQueuePlug) -> None:
        self._queue = Queue()
        self._id = plug.registerTaskQueue(self)
        
    def id(self) -> int:
        return self._id
    
    def readerProcessId(self):
        raise NotImplementedError()
    
    def put(self, task: Task):
        self._queue.put(task)
        
    def get(self) -> Task:
        return self._queue.get()

    
    