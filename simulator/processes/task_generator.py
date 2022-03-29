from abc import abstractmethod
from collections import deque
from simulator.core.task import Task
from simulator.config import Config
from simulator.common import Common
from simulator.core.process import Process
import numpy as np

class TaskGeneratorPlug:
    
    @abstractmethod
    def fetchTaskDistributionTimeQueue(self, processId: int) -> deque:
        pass
    
    @abstractmethod
    def taskNodeId(self, processId: int) -> int:
        pass
    
    @abstractmethod
    def taskArrival(self, task: Task, processId: int) -> None:
        pass
    
class TaskGenerator(Process):
    def __init__(self, plug: TaskGeneratorPlug) -> None:
        super().__init__()
        self._plug = plug
        self._loadCongif()
        
    def _loadCongif(self):
        self._task_size_kBit = Config.get("task_size_kBit")
        self._task_size_sd_kBit = Config.get("task_size_sd_kBit")
        self._task_size_min_kBit = Config.get("task_size_min_kBit")
        self._task_kflops_per_bit = Config.get("task_kflops_per_bit")
        self._task_kflops_per_bit_sd = Config.get("task_kflops_per_bit_sd")
        self._task_kflops_per_bit_min = Config.get("task_kflops_per_bit_min")
    
    def wake(self) -> None:
        super().wake()
        timeQueue = self._plug.fetchTaskDistributionTimeQueue(self.id())
        while(len(timeQueue) > 0 and timeQueue[0] <= Common.time()):
            timeQueue.popleft()
            #TODO task should have more variables such as arrival time which should be taken from time queue
            taskSize = np.random.normal(self._task_size_kBit, self._task_size_sd_kBit) * 1000
            taskSize = int(max([self._task_size_min_kBit * 1000, taskSize]))
            flops = np.random.normal(self._task_kflops_per_bit, self._task_kflops_per_bit_sd) * 1000
            flops = int(max([self._task_kflops_per_bit_min * 1000, flops]))
            newTask = Task(size=taskSize, workload=flops, nodeId=self._plug.taskNodeId(self._id))
            self._plug.taskArrival(newTask, self._id)