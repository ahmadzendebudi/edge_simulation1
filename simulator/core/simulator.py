
import numpy as np
from simulator.core import EventHeap
from simulator import Config
from simulator import Common
from simulator.core.environment import Environment
from simulator.core.process import Process
from simulator.core.task import Task
from simulator.core.task_queue import TaskQueue
from simulator.core.node import Node

class Simulator:
    def __init__(self) -> None:
        np.random.seed(Config.get('random_seed'))
        self._eventHeap = EventHeap()
        self._processMap = {}
        self._taskQueueMap = {}
        self._nodeMap = {}
        self._taskMap = {}
    
    def setup(self, env: Environment):
        self._env = env
    
    def registerTaskQueue(self, taskQueue: TaskQueue) -> int:
        id = Common.generateUniqueId()
        taskQueue.setup(id)
        self._taskQueueMap[id] = taskQueue
        return id
    
    def registerProcess(self, process: Process) -> int:
        id = Common.generateUniqueId()
        process.setup(id)
        self._processMap[id] = process
        return id
    
    def registerNode(self, node: Node):
        id = Common.generateUniqueId()
        node.setup(id)
        self._nodeMap[id] = node
        return id
    
    def registerTask(self, task: Task):
        id = Common.generateUniqueId()
        task.setup(id)
        self._taskMap[id] = task
        return id
    
    def unregisterTask(self, taskId: int) -> Task:
        return self._taskMap.pop(taskId)
        
    def getProcess(self, id: int) -> Process:
        return self._processMap[id]
    
    def getTaskQueue(self, id: int) -> TaskQueue:
        return self._taskQueueMap[id]
    
    def getTask(self, id: int) -> Task:
        return self._taskMap[id]
    
    def getNode(self, id: int) -> Node:
        return self._nodeMap[id]
    
    def registerEvent(self, time: int, processId: int) -> None:
        self._eventHeap.addEvent(time, processId)
    
        