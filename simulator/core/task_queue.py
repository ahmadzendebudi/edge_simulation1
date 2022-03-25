
from simulator.core.task import Task
from queue import Queue

class TaskQueue:
    def __init__(self, readerProcessId: int) -> None:
        self._readerProcessId = readerProcessId
        self._queue = Queue()
        
    def setup(self, id: int) -> None:
        self._id = id
        
    def id(self) -> int:
        return self._id
    
    def readerProcessId(self):
        return self._readerProcessId
    
    def put(self, task: Task):
        self._queue.put(task)
        
    def get(self) -> Task:
        return self._queue.get()

    
    