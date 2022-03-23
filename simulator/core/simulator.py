from simulator.core.event_heap import EventHeap

class Simulator:
    def __init__(self) -> None:
        self._eventHeap = EventHeap()
        self._processMap = {}
        
        