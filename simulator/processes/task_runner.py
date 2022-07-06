
from abc import abstractmethod
from simulator.common import Common
from simulator.core.process import Process
from simulator.core.task import Task
from simulator.core.task_queue import TaskQueue

class TaskRunnerPlug:
    @abstractmethod
    def fetchTaskRunnerQueue(self, processId: int) -> TaskQueue:
        pass
    
    @abstractmethod
    def wakeTaskRunnerAt(self, time: int, processId: int):
        pass
    
    @abstractmethod
    def taskRunComplete(self, task: Task, processId: int):
        pass

class TaskRunner(Process):
    def __init__(self, plug: TaskRunnerPlug, flops: int, metteredPowerConsumttionPerTflops: float = 0) -> None:
        '''flops: floating point operation per second for the host device'''
        super().__init__()
        self._plug = plug
        self._liveTask = None
        self._liveTaskCompletionTime = None
        self._liveTaskPowerConsumption = None
        self._flops = flops
        self._powerConsumttionPerTflops = metteredPowerConsumttionPerTflops
        
    def wake(self) -> None:
        if (self._liveTask != None and self._liveTaskCompletionTime <= Common.time()):
            self._liveTask.powerConsumed += self._liveTaskPowerConsumption
            self._plug.taskRunComplete(self._liveTask, self._id)
            self._liveTask = None
            self._liveTaskCompletionTime = None
            self._liveTaskPowerConsumption = None
        
        if (self._liveTask is None):
            queue = self._plug.fetchTaskRunnerQueue(self._id)
            if queue.qsize() != 0:
                self._runTask(queue.get())
        return super().wake()
    
    def _runTask(self, task: Task):
        self._liveTask = task
        self._liveTaskCompletionTime = Common.time() + task.workload() / self._flops
        self._liveTaskPowerConsumption = task.workload() * self._powerConsumttionPerTflops / (10 ** 12)
        self._plug.wakeTaskRunnerAt(self._liveTaskCompletionTime, self._id)
    
    def remainingWorkloadForCurrentTask(self) -> int:
        workload = 0
        if (self._liveTask != None):
            workload += self._flops * (self._liveTaskCompletionTime - Common.time())
        return workload
    
    def liveTask(self):
        return self._liveTask

    @classmethod
    def remainingWorkloadTaskQueue(cls, taskQueue: TaskQueue) -> int:
        workload = 0
        for task in taskQueue.deque():
            workload += task.workload()
        return workload

        