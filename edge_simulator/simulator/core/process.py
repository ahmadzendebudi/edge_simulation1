from abc import abstractmethod


class Process:
    def processId() -> int:
        pass
    
    @abstractmethod
    def wake():
        pass