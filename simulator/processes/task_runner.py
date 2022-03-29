
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
    def __init__(self, plug: TaskRunnerPlug, flops: int) -> None:
        '''flops: floating point operation per second for the host device'''
        super().__init__()
        self._plug = plug
        self._liveTask = None
        self._liveTaskCompletionTime = None
        self._flops = flops
        
    def wake(self) -> None:
        if (self._liveTask != None and self._liveTaskCompletionTime <= Common.time()):
            self._plug.taskRunComplete(self._liveTask, self._id)
            self._liveTask = None
            self._liveTaskCompletionTime = None
        
        if (self._liveTask == None):
            queue = self._plug.fetchTaskRunnerQueue(self._id)
            if queue.qsize() != 0:
                self._runTask(queue.get())
        return super().wake()
    
    def _runTask(self, task: Task):
        self._liveTask = task
        self._liveTaskCompletionTime = Common.time() + task.size() * task.workload() / self._flops
        self._plug.wakeTaskRunnerAt(self._liveTaskCompletionTime, self._id)
        