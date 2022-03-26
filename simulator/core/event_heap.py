from typing import Tuple
import heapq

class EventHeap:
    
    def __init__(self) -> None:
        self._heap = []
        heapq.heapify(self._heap)
    
    def addEvent(self, time: int, processId: int) -> None:
        heapq.heappush(self._heap, EventHeap._Event(time, processId))
    
    def nextEvent(self) -> Tuple[int, int]:
        '''returns (time: int, processId: int)'''
        event = heapq.heappop(self._heap)
        return (event._time, event._processId)
    
    def size(self) -> int:
        return len(self._heap)
    
    class _Event:
        def __init__(self, time: int, processId: int) -> None:
            self._time = time
            self._processId = processId
        
        def __eq__(self, __o: object) -> bool:
            return self._time == __o._time
        
        def __ne__(self, __o: object) -> bool:
            return self._time != __o._time
        
        def __lt__(self, __o: object) -> bool:
            return self._time < __o._time
        
        def __gt__(self, __o: object) -> bool:
            return self._time > __o._time
        
        def __le__(self, __o: object) -> bool:
            return self._time <= __o._time
        
        def __ge__(self, __o: object) -> bool:
            return self._time >= __o._time
        