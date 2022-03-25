from abc import abstractmethod

class ProcessPlug:
    @abstractmethod
    def registerProcess(self, process) -> int:
        pass
class Process:
    def __init__(self, plug: ProcessPlug) -> None:
        self._processId = plug.registerProcess(self)
    
    def processId(self) -> int:
        return self._processId
    
    @abstractmethod
    def wake(self) -> None:
        pass