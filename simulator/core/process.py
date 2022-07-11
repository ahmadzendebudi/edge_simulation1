from abc import abstractmethod

class Process:
    def __init__(self, extends_runtime = True) -> None:
        self._extends_runtime = extends_runtime
    
    def setup(self, id: int):
        self._id = id
    
    def id(self) -> int:
        return self._id
    
    @abstractmethod
    def wake(self) -> None:
        pass