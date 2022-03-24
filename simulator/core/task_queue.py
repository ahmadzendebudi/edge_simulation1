from simulator.core import Task
from queue import Queue

class TaskQueue:
    def __init__(self, id) -> None:
        self._queue = Queue()
        self._id = id
        
    def id(self) -> int:
        return self._id
    
    def readerProcessId(self):
        raise NotImplementedError()
    
    def put(self, task: Task):
        self._queue.put(task)
        
    def get(self) -> Task:
        return self._queue.get()

    
    