
from xmlrpc.client import boolean
from simulator.core.task import Task
from collections import deque

class TaskQueue:
    def __init__(self) -> None:
        self._queue = deque()
        
    def setup(self, id: int) -> None:
        self._id = id
        
    def id(self) -> int:
        return self._id
    
    def put(self, task: Task):
        self._queue.append(task)
        
    def qsize(self) -> int:
        return len(self._queue)
    
    def get(self) -> Task:
        return self._queue.popleft()

    
    