from abc import abstractmethod
from simulator.core import Node
from simulator.core import TaskQueue
from simulator.core.simulator import Simulator
from simulator.core.task import Task
from simulator.task_multiplexing.state_handler import StateHandler
from simulator.task_multiplexing.transition import Transition
from simulator.task_multiplexing.transition_recorder import TransitionRecorder, TwoStepTransitionRecorder
from simulator.processes.task_runner import TaskRunner, TaskRunnerPlug

class TaskNode(Node, StateHandler, TaskRunnerPlug):
    def __init__(self, externalId: int, flops: int, cores: int, 
                 transitionRecorder: TwoStepTransitionRecorder = None, 
                 metteredPowerConsumtionPerTFlops: float = 0) -> None:
        super().__init__(externalId)
        self._flops = flops
        self._cores = cores
        self._transitionRecorder = transitionRecorder
        self._metteredPowerConsumtionPerTFlops = metteredPowerConsumtionPerTFlops
    
    def setTransitionRecorder(self, transitionRecorder: TransitionRecorder):
        self._transitionRecorder = transitionRecorder
    
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
    def initializeConnection(self, simulator: Simulator):
        pass
    
    def initializeProcesses(self, simulator: Simulator):
        self._simulator = simulator
        self._localQueue = TaskQueue()
        simulator.registerTaskQueue(self._localQueue)
        self._taskRunners = []
        for _ in range(0, self._cores):
            taskRunner = TaskRunner(self, self._flops, self._metteredPowerConsumtionPerTFlops)
            simulator.registerProcess(taskRunner)
            self._taskRunners.append(taskRunner)
    
    def recordTransition(self, task: Task, state1, state2, actionObject) -> None:
        if (self._transitionRecorder != None):
            transition = Transition(task.id(), state1, state2, actionObject)
            self._transitionRecorder.put(transition)
    