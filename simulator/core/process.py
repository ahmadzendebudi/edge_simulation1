from abc import abstractmethod


class Process:
    def __init__(self, processId: int) -> None:
        self._processId = processId
    
    def processId(self) -> int:
        return self._processId
    
    @abstractmethod
    def wake(self) -> None:
        pass