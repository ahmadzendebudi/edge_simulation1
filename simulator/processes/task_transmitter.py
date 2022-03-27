
from abc import abstractmethod
from simulator.common import Common
from simulator.core.connection import Connection
from simulator.core.process import Process
from simulator.core.task import Task
from simulator.core.task_queue import TaskQueue

class TaskTransmitterPlug:
    @abstractmethod
    def fetchTaskTransmitterQueue(self, processId: int) -> TaskQueue:
        pass
    
    @abstractmethod
    def fetchDestinationConnection(self, processId: int) -> Connection:
        pass
    
    @abstractmethod
    def taskTransmissionComplete(self, task: Task, processId: int) -> int:
        pass
    
    @abstractmethod
    def wakeTaskTransmitterAt(self, time: int, processId: int) -> None:
        pass

class TaskTransmitter(Process):
    def __init__(self, plug: TaskTransmitterPlug) -> None:
        super().__init__()
        self._plug = plug
        self._liveTask = None
        self._liveTaskCompletionTime = None
        
    def wake(self) -> None:
        if (self._liveTask != None and self._liveTaskCompletionTime <= Common.time()):
            self._plug.taskTransmissionComplete(self._liveTask, self._id)
            self._liveTask = None
            self._liveTaskCompletionTime = None
        
        if (self._liveTask == None):
            queue = self._plug.fetchTaskTransmitterQueue(self._id)
            if queue.qsize() != 0:
                self._transmitTask(queue.get())
        return super().wake()
    
    def _transmitTask(self, task: Task):
        #TODO I need to calculate task transmit duration properly!
        self._liveTask = task
        connection = self._plug.fetchDestinationConnection(self._id)
        self._liveTaskCompletionTime = Common.time() + task.size() / connection.bandwidth()
        self._plug.wakeTaskTransmitterAt(self._liveTaskCompletionTime, self._id)