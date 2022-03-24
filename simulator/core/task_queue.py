from simulator.core import Task
from queue import Queue

class TaskQueue:
    def __init__(self) -> None:
        self._queue = Queue()
    
    def readerProcessId(self):
        raise NotImplementedError()
    
    def put(self, task: Task):
        self._queue.put(task)
        
    def get(self) -> Task:
        return self._queue.get()

    
    