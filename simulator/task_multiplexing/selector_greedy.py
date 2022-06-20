
from collections import deque
from typing import Any, Callable, Sequence
from simulator.config import Config
from simulator.core.task import Task
from simulator.logger import Logger
from simulator.task_multiplexing.selector import TaskMultiplexerSelector
from simulator.task_multiplexing.transition import Transition


class TaskMultiplexerSelectorGreedy(TaskMultiplexerSelector):
    def __init__(self, state, rewardFunction: Callable[[Transition], float]) -> None:
        super().__init__(rewardFunction)
        if Config.get("mode_workload_provided"):
            if (state == (10,)):
                self._localFlops = Config.get("mobile_cpu_core_tflops") * 10 ** 12
                self._localCores = Config.get("mobile_cpu_cores")
                self._remoteFlops = Config.get("edge_cpu_core_tflops") * 10 ** 12
                self._remoteCores = Config.get("edge_cpu_cores")
                
                self._taskWorkloadIndex = 1
                self._dataRateIndex = 2
                self._localWorkloadIndex = 3
                self._localTransferWorkloadIndex = 5
                self._localTransferSizeIndex = 6
                self._remoteWorkloadIndex = 8
            else:
                self._localFlops = Config.get("edge_cpu_core_tflops") * 10 ** 12
                self._localCores = Config.get("edge_cpu_cores")
                self._remoteFlops = Config.get("edge_cpu_core_tflops") * 10 ** 12
                self._remoteCores = Config.get("edge_cpu_cores")
                
                self._taskWorkloadIndex = 2
                self._dataRateIndex = 3
                self._localWorkloadIndex = 4
                self._localTransferWorkloadIndex = 6
                self._localTransferSizeIndex = 7
                self._remoteWorkloadIndex = 9
        else:
            if (state == (6,)):
                self._localFlops = Config.get("mobile_cpu_core_tflops") * 10 ** 12
                self._localCores = Config.get("mobile_cpu_cores")
                self._remoteFlops = Config.get("edge_cpu_core_tflops") * 10 ** 12
                self._remoteCores = Config.get("edge_cpu_cores")
                
                self._taskSizeIndex = 0
                self._dataRateIndex = 1
                self._localQueueSizeIndex = 2
                self._localTransferSizeIndex = 3
                self._localTransferQueueSizeIndex = 4
                self._remoteQueueSizeIndex = 5
            else:
                self._localFlops = Config.get("edge_cpu_core_tflops") * 10 ** 12
                self._localCores = Config.get("edge_cpu_cores")
                self._remoteFlops = Config.get("edge_cpu_core_tflops") * 10 ** 12
                self._remoteCores = Config.get("edge_cpu_cores")
                
                
                self._taskSizeIndex = 0
                self._dataRateIndex = 2
                self._localQueueSizeIndex = 3
                self._localTransferSizeIndex = 4
                self._localTransferQueueSizeIndex = 5
                self._remoteQueueSizeIndex = 6
        
        self._wattsPerFlop = Config.get("mobile_watts_per_tflop") / (10 ** 12)
        self._wattsPerTransmitSecond = Config.get("mobile_transmit_power_watts")
        #self._normalTaskWorkload will be updated after transitions arrive at addToBuffer method (if workload not provided)
        self._normalTaskWorkload = Config.get("task_size_kBit") * Config.get("task_kflops_per_bit") * 10 ** 6
        
        self._delayCoefficient = Config.get("delay_coefficient")
        self._powerCoefficient = Config.get("power_coefficient")
        self._normalTaskSize = 10 ** 6
        self._transitionBuffer = deque()
        
    def action(self, task: Task, state: Sequence[float]) -> Any:
        #TODO make use of task
        localRun = None
        transfer = None
        remoteRun = None
        powerLocal = None
        powerRemote = None
        if Config.get("mode_workload_provided"):
            localRun = state[self._localWorkloadIndex] * self._normalTaskWorkload / self._localFlops
            transfer = state[self._localTransferSizeIndex] / state[self._dataRateIndex]
            remoteRun = ((state[self._localTransferWorkloadIndex] + state[self._remoteWorkloadIndex]) *
                        self._normalTaskWorkload / (self._remoteFlops * self._remoteCores))
            powerLocal = state[self._localWorkloadIndex] * self._normalTaskWorkload * self._wattsPerFlop
            powerRemote = transfer * self._wattsPerTransmitSecond
        else:
            localRun = state[self._localQueueSizeIndex] * self._normalTaskWorkload / self._localFlops
            transfer = state[self._localTransferSizeIndex] / state[self._dataRateIndex]
            remoteRun = ((state[self._localTransferQueueSizeIndex] + state[self._remoteQueueSizeIndex]) *
                        self._normalTaskWorkload / (self._remoteFlops * self._remoteCores))
            powerLocal = state[self._localQueueSizeIndex] * self._normalTaskWorkload * self._wattsPerFlop
            powerRemote = transfer * self._wattsPerTransmitSecond
            
        action = (self._delayCoefficient * localRun + self._powerCoefficient * powerLocal >
                self._delayCoefficient * (transfer + remoteRun) + self._powerCoefficient *  powerRemote)
        
        if action == True:
            return action, 1
        else:
            return action, None    
    
        
    def _addToBuffer(self, transition: Transition) -> None:
        self._transitionBuffer.append(transition)
        if (len(self._transitionBuffer) > 2000):
            self._transitionBuffer.popleft()
        if not Config.get("mode_workload_provided"):
            self._normalTaskWorkload = sum(map(lambda x: x.taskWorkload, self._transitionBuffer))/ len(self._transitionBuffer)
        Logger.log("addToBuffer, normalworkload:" + str( self._normalTaskWorkload ), 2)