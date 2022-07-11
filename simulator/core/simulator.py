
import numpy as np
from simulator.core import EventHeap
from simulator import Config
from simulator import Common
from simulator.core.connection import Connection
from simulator.core.environment import Environment
from simulator.core.parcel import Parcel
from simulator.core.parcel_queue import ParcelQueue
from simulator.core.process import Process
from simulator.core.task import Task
from simulator.core.task_queue import TaskQueue
from simulator.core.node import Node

class Simulator:
    def __init__(self) -> None:
        Common.setTime(0)
        self._eventHeap = EventHeap()
        self._processMap = {}
        self._taskQueueMap = {}
        self._nodeMap = {}
        self._taskMap = {}
        self._connectionMap = {}
        self._parcelQueueMap = {}
        self._runtime_extension = Config.get("task_generation_duration")
    
    def run(self):
        eventHeap = self._eventHeap
        time = 0
        while eventHeap.size() > 0 and time <= self._runtime_extension:
            time, processId = eventHeap.nextEvent()
            Common.setTime(time)
            eventProcess = self.getProcess(processId)
            if eventProcess != None:
                eventProcess.wake()
            
    
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

    def unregisterProcess(self, processId: int) -> Process:
        return self._processMap.pop(processId)
    
    def registerNode(self, node: Node):
        id = Common.generateUniqueId()
        node.setup(id)
        self._nodeMap[id] = node
        self._processMap[id] = node
        return id
    
    def registerTask(self, task: Task):
        id = Common.generateUniqueId()
        task.setup(id)
        self._taskMap[id] = task
        return id
    
    def registerParcelQueue(self, parcelQueue: ParcelQueue):
        id = Common.generateUniqueId()
        parcelQueue.setup(id)
        self._parcelQueueMap[id] = parcelQueue
        return id
    
    def unregisterParcelQueue(self, id: int) -> ParcelQueue:
        return self._parcelQueueMap.pop(id)
    
    def unregisterTask(self, taskId: int) -> Task:
        return self._taskMap.pop(taskId)
    
    def getProcess(self, id: int) -> Process:
        return self._processMap.get(id, None)
    
    def getTaskQueue(self, id: int) -> TaskQueue:
        return self._taskQueueMap[id]
    
    def getTask(self, id: int) -> Task:
        return self._taskMap[id]
    
    def getNode(self, id: int) -> Node:
        return self._nodeMap[id]
    
    def registerEvent(self, time: int, processId: int) -> None:
        self._eventHeap.addEvent(time, processId)
        if self.getProcess(processId)._extends_runtime and self._runtime_extension < time:
            self._runtime_extension = time
        
    def getParcelQueue(self, id: int) -> TaskQueue:
        return self._parcelQueueMap[id]
    
    def sendParcel(self, parcel: Parcel, destNodeId: int) -> None:
        destNode = self.getNode(destNodeId)
        destNode.parcelInbox(parcel)
        self.registerEvent(Common.time(), destNodeId)
    
        