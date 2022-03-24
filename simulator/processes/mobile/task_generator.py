from ast import walk
from simulator import core
from simulator import environment as env
from simulator import Config
from simulator import Common

class TaskGenerator(core.Process):
    def __init__(self, processId: int, env: env.TaskEnvironment, mobileNode: env.MobileNode) -> None:
        super().__init__(processId)
        self._env = env
        self._mobileNode = mobileNode
        self._taskGenerationTime = Common.time()
        self._prefetchTime = Config.get("task_generator_prefetch_time")
        self._lambda = Config.get("task_generator_lambda")
        self.wake()
      
    def wake(self) -> None:
        #TODO generate tasks until Common.time() + prefeetchTime
        super().wake()