from abc import abstractmethod
from typing import Sequence, Tuple
import simulator
from simulator.common import Common
from simulator.config import Config
from simulator.core import Node
from simulator.core import Connection
from simulator.core import TaskQueue
from simulator.core.parcel import Parcel
from simulator.core.parcel_queue import ParcelQueue
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.core.task import Task
from simulator.logger import Logger
from simulator.processes.task_multiplexer import TaskMultiplexer, TaskMultiplexerPlug, TaskMultiplexerSelectorLocal, TaskMultiplexerSelectorRandom
from simulator.processes.task_runner import TaskRunner, TaskRunnerPlug
from simulator.processes.parcel_transmitter import ParcelTransmitter, ParcelTransmitterPlug

class TaskNode(Node, TaskRunnerPlug):
    def __init__(self, externalId: int, flops: int, cores: int) -> None:
        super().__init__(externalId)
        self._flops = flops
        self._cores = cores
    
    @abstractmethod
    def initializeConnection(self, simulator: Simulator):
        pass
    
    def initializeProcesses(self, simulator: Simulator):
        self._simulator = simulator
        self._localQueue = TaskQueue()
        simulator.registerTaskQueue(self._localQueue)
        self._taskRunners = []
        for _ in range(0, self._cores):
            taskRunner = TaskRunner(self, self._flops)
            simulator.registerProcess(taskRunner)
            self._taskRunners.append(taskRunner)
    
    def currentWorkload(self):
        workload = TaskRunner.remainingWorkloadTaskQueue(self._localQueue)
        for taskRunner in self._taskRunners:
            workload += taskRunner.remainingWorkloadForCurrentTask()
        return workload
    
    def fetchTaskRunnerQueue(self, processId: int) -> TaskQueue:
        return self._localQueue
    
    def wakeTaskRunnerAt(self, time: int, processId: int):
        self._simulator.registerEvent(time, processId)
    
    @abstractmethod
    def taskRunComplete(self, task: Task, processId: int):
        pass