
import numpy as np
from simulator.core import EventHeap
from simulator.core import Environment
from simulator.core import ProcessPlug
from simulator.core import TaskQueuePlug
from simulator import Config
from simulator import Common

class Simulator(ProcessPlug, TaskQueuePlug):
    def __init__(self) -> None:
        np.random.seed(Config.get('random_seed'))
        self._eventHeap = EventHeap()
        self._processMap = {}
        self._taskQueueMap = {}
    
    def setup(self, env: Environment):
        self._env = env
    
    def registerTaskQueue(self, taskQueue) -> int:
        id = Common.generateUniqueId()
        self._taskQueueMap[id] = taskQueue
        return id
    
    def registerProcess(self, process) -> int:
        id = Common.generateUniqueId()
        self._processMap[id] = process
        return id
    
    def getProcess(self, id: int):
        return self._processMap[id]
    
    def getTaskQueue(self, id: int):
        return self._taskQueueMap[id]
    
    def registerEvent(self, time: int, processId: int) -> None:
        self._eventHeap.addEvent(time, processId)
    
        