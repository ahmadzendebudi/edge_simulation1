from abc import abstractmethod

class Process:
    def __init__(self) -> None:
        pass
    
    def setup(self, id: int):
        self._id = id
    
    def id(self) -> int:
        return self._id
    
    @abstractmethod
    def wake(self) -> None:
        pass