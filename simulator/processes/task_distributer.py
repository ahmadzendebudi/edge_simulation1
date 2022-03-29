from abc import abstractmethod
from simulator.config import Config
from simulator.common import Common
from simulator.core.process import Process
import numpy as np

class TaskDistributerPlug:
    @abstractmethod
    def registerTask(self, time: int, processId: int) -> None:
        pass
    
    @abstractmethod
    def wakeTaskDistributerAt(self, time: int, processId: int) -> None:
        pass
    
class TaskDistributer(Process):
    def __init__(self, plug: TaskDistributerPlug) -> None:
        super().__init__()
        self._plug = plug
        self._taskGenerationTime = Common.time()
        self._prefetchTime = Config.get("task_generator_prefetch_time")
        self._lambda = Config.get("task_generator_lambda")
        self._simulationDuration = Config.get("task_generation_duration")
    
    def wake(self) -> None:
        while (self._taskGenerationTime < Common.time() + self._prefetchTime and
               self._taskGenerationTime < self._simulationDuration):
            self._taskGenerationTime += np.random.exponential(1/self._lambda)
            if (self._taskGenerationTime < self._simulationDuration):
                self._plug.registerTask(self._taskGenerationTime, self._id)
        if (self._taskGenerationTime < self._simulationDuration):
            self._plug.wakeTaskDistributerAt(self._taskGenerationTime)
        super().wake()