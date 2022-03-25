from abc import abstractmethod
from simulator.core.task import Task
from simulator.config import Config
from simulator.common import Common
from simulator.core.process import Process
import numpy as np

class TaskGeneratorPlug:
    
    @abstractmethod
    def taskNodeId(self) -> int:
        pass
    
    @abstractmethod
    def taskArrival(self, task: Task) -> None:
        pass
    
class TaskGenerator(Process):
    def __init__(self, plug: TaskGeneratorPlug) -> None:
        super().__init__()
        self._plug = plug
        
    
    def wake(self) -> None:
        super().wake()
        #TODO these variables should be changed to match simulation criteria
        newTask = Task(size=1, workload=1, nodeId=self._plug.taskNodeId())
        self._plug.taskArrival(newTask)