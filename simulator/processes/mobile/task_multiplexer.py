
from abc import abstractmethod
from simulator.core.process import Process

class TaskMultiplexerPlug:
    @abstractmethod
    def taskLocalExecution(self, taskId: int) -> None:
        pass
    
    @abstractmethod
    def taskTransimission(self, taskId: int) -> None:
        pass
    
class TaskMultiplexer(Process):
    
    def __init__(self, plug: TaskMultiplexerPlug) -> None:
        super().__init__()
        self._plug = plug
        