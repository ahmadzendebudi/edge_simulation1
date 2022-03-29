
from simulator.core.parcel import Parcel
from collections import deque

class ParcelQueue:
    def __init__(self) -> None:
        self._queue = deque()
        
    def setup(self, id: int) -> None:
        self._id = id
        
    def id(self) -> int:
        return self._id
    
    def put(self, Parcel: Parcel):
        self._queue.append(Parcel)
        
    def qsize(self) -> int:
        return len(self._queue)
    
    def get(self) -> Parcel:
        return self._queue.popleft()

    
    