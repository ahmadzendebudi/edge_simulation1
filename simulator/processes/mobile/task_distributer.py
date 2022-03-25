from abc import abstractmethod
from simulator.config import Config
from simulator.common import Common
from simulator.core.process import Process
import numpy as np

class TaskDistributerPlug:
    @abstractmethod
    def registerTask(self, time: int) -> None:
        pass
    
class TaskDistributer(Process):
    def __init__(self, plug: TaskDistributerPlug) -> None:
        super().__init__()
        self._plug = plug
        self._taskGenerationTime = Common.time()
        self._prefetchTime = Config.get("task_generator_prefetch_time")
        self._lambda = Config.get("task_generator_lambda")
        self.wake()
    
    def wake(self) -> None:
        #TODO generate tasks until Common.time() + prefeetchTime
        while (self._taskGenerationTime < Common.time() + self._prefetchTime):
            self._taskGenerationTime += np.random.exponential(1/self._lambda)
            self._plug.registerTask(self._taskGenerationTime)
        super().wake()