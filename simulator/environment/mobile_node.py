from abc import abstractmethod
from collections import deque
from typing import Any, Callable, Sequence, Tuple

from simulator.common import Common
from simulator.config import Config
from simulator.core.connection import Connection
from simulator.core.parcel import Parcel
from simulator.core.parcel_queue import ParcelQueue
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.core.task_queue import TaskQueue
from simulator.core.task import Task
from simulator.environment.task_node import TaskNode
from simulator.task_multiplexing.transition_recorder import TransitionRecorder
from simulator.logger import Logger
from simulator.processes.task_distributer import TaskDistributer, TaskDistributerPlug
from simulator.processes.task_generator import TaskGenerator, TaskGeneratorPlug
from simulator.processes.task_multiplexer import TaskMultiplexer, TaskMultiplexerPlug, TaskMultiplexerSelector
from simulator.processes.parcel_transmitter import ParcelTransmitter, ParcelTransmitterPlug

class MobileNodePlug:
    @abstractmethod
    def updateMobileNodeConnection(self, nodeId: int, nodeExternalId: int) -> Tuple[Connection, int]:
        '''Should return the current connection and the maximum duration before which
        this function is called again'''
        pass

class TaskMultiplexerSelectorMobile(TaskMultiplexerSelector):
    def __init__(self, innerSelector: TaskMultiplexerSelector, destId: int) -> None:
        self._innerSelector = innerSelector
        self._destId = destId
        super().__init__()
    
    def action(self, task: Task, state: Sequence[float]) -> Any:
        return self._innerSelector.action(task, state)
    
    def select(self, action: Any) -> int:
        selection = self._innerSelector.select(action)
        if selection == 1:
            return self._destId
        elif selection == None or selection == 0:
            return None
        else:
            raise ValueError("output selection: " + str(selection) + " is not supported by this selector")
            
            
class MobileNode(TaskNode, TaskDistributerPlug, TaskGeneratorPlug, TaskMultiplexerPlug, ParcelTransmitterPlug):
    def __init__(self, externalId: int, plug: MobileNodePlug, flops: int, cores: int,
                 metteredPowerConsumtionPerTFlops: float = 0) -> None:
        self._plug = plug
        self._edgeState = [0, 0]
        super().__init__(externalId, flops, cores, metteredPowerConsumtionPerTFlops)
    
    def edgeConnection(self) -> Connection:
        self._edgeConnection
    
    def initializeConnection(self, simulator: Simulator):
        self._simulator = simulator
        self._edgeConnection, duration = self._plug.updateMobileNodeConnection(self.id(), self.externalId())
        self._connectionProcess = Process()
        self._connectionProcess.wake = self.updateConnection
        simulator.registerProcess(self._connectionProcess)
        if (duration != None):
            simulator.registerEvent(Common.time() + duration, self._connectionProcess.id())
    
    def updateConnection(self):
        self._edgeConnection, duration = self._plug.updateMobileNodeConnection(self.id(), self.externalId())
        if (duration != None):
            self._simulator.registerEvent(Common.time() + duration, self._connectionProcess.id())
        
    def initializeProcesses(self, simulator: Simulator, multiplexSelector: TaskMultiplexerSelector):
        super().initializeProcesses(simulator)
        
        self._taskDistributer = TaskDistributer(self)
        simulator.registerProcess(self._taskDistributer)
        simulator.registerEvent(Common.time(), self._taskDistributer.id())
        
        self._taskDistributionTimeQueue = deque()
        self._taskGenerator = TaskGenerator(self)
        simulator.registerProcess(self._taskGenerator)
        
        mobileMultiplexSelector = TaskMultiplexerSelectorMobile(
            multiplexSelector, self._edgeConnection.destNode())
        self._taskMultiplexer = TaskMultiplexer(self, mobileMultiplexSelector, self)
        simulator.registerProcess(self._taskMultiplexer)
        self._multiplexQueue = TaskQueue()
        simulator.registerTaskQueue(self._multiplexQueue)
        
        self._transmitQueue = ParcelQueue()
        simulator.registerParcelQueue(self._transmitQueue)
        self._transmitter = ParcelTransmitter(self._simulator, self._transmitQueue, self)
        simulator.registerProcess(self._transmitter)
        
    #Task Distributer
    def registerTask(self, time: int, processId: int) -> None:
        self._taskDistributionTimeQueue.append(time)
        self._simulator.registerEvent(time, self._taskGenerator.id())
    
    def wakeTaskDistributerAt(self, time: int, processId: int) -> None:
        self._simulator.registerEvent(time, self._taskDistributer.id())
    
    #Task Generator
    def fetchTaskDistributionTimeQueue(self, processId: int) -> deque:
        return self._taskDistributionTimeQueue
    
    def taskNodeId(self, processId: int) -> int:
        return self._id
    
    def taskArrival(self, task: Task, processId: int) -> None:
        self._simulator.registerTask(task)
        self._multiplexQueue.put(task)
        self._simulator.registerEvent(Common.time(), self._taskMultiplexer.id())
    
    #State handler:
    def fetchState(self, task: Task, processId: int) -> Sequence[float]:
        return self._generateState(task, self._edgeConnection.datarate(), 
                self.currentWorkload(), self._localQueue.qsize(),
                self._transmitter.remainingTransmitWorkload(),
                self._transmitter.remainingTransmitSize(),
                self._transmitQueue.qsize(),
                self._edgeState[0], self._edgeState[1])
    
    
    def fetchTaskInflatedState(self, task: Task, processId: int) -> Sequence[float]:
        taskWorkload = task.size() * task.workload()
        return self._generateState(task, self._edgeConnection.datarate(),
                self.currentWorkload() + taskWorkload, self._localQueue.qsize() + 1,
                self._transmitter.remainingTransmitWorkload() + taskWorkload,
                self._transmitter.remainingTransmitSize() + task.size(),
                self._transmitQueue.qsize() + 1,
                self._edgeState[0], self._edgeState[1])
    
    def _generateState(self, task: Task, datarate: int, localWorkload: int, localQueueSize: int,
                        localTransferWorkload: int, localTransferSize: int, localTransferQueueSize: int, 
                        remoteWorkload: int, remoteQueueSize: int):
        normalTaskWorkload = Config.get("task_size_kBit") * Config.get("task_kflops_per_bit") * 10 ** 6
        normalTaskSize = 10 ** 6
        return [task.size() * task.workload() / normalTaskWorkload, datarate / normalTaskSize,
                localWorkload / normalTaskWorkload, localQueueSize,
                localTransferWorkload / normalTaskWorkload, localTransferSize / normalTaskSize, localTransferQueueSize,
                remoteWorkload/normalTaskWorkload, remoteQueueSize]
    
    @classmethod
    def fetchStateShape(cls) -> Tuple[int]:
        return (9,)
    
    #Task multiplexer plug:
    def fetchMultiplexerQueue(self, processId: int) -> TaskQueue:
        return self._multiplexQueue
    
    def taskLocalExecution(self, task: Task, processId: int) -> None:
        self._localQueue.put(task)
        for taskRunner in self._taskRunners:
            self._simulator.registerEvent(Common.time(), taskRunner.id())
    
    def taskTransimission(self, task: Task, processId: int, destinationId: int) -> None:
        if self._edgeConnection.destNode() != destinationId:
            raise ValueError("destination ids do not match, something most have gone wrong" +
                             "received dest id:" + str(destinationId) + ", mobile node dest id" +
                             str(self._edgeConnection.destNode()))
        parcel = Parcel(Common.PARCEL_TYPE_TASK, task.size(), task, self._id, task.size() * task.workload())
        self._transmitter.transmitQueue().put(parcel)
        self._simulator.registerEvent(Common.time(), self._transmitter.id())
        #approximating the work load in edge by adding the current task to the last state report:
        #no longer needed, as the task will either be in run queue or transmit queue and both are used for state
        #self._edgeState = [self._edgeState[0] + task.size() * task.workload(), self._edgeState[1] + 1]
    
    #Task Runner:
    def taskRunComplete(self, task: Task, processId: int):
        self._taskCompleted(task)
    
    def _taskCompleted(self, task: Task) -> None:
        delay = Common.time() - task.arrivalTime()
        self._transitionRecorder.completeTransition(task.id(), delay, task.powerConsumed)
        if Logger.levelCanLog(2):
            Logger.log("Run Complete: " + str(task), 2)
    
    #Task Transmitter
    def fetchDestinationConnection(self, processId: int) -> Connection:
        return self._edgeConnection
    
    def parcelTransmissionComplete(self, parcel: Parcel, processId: int) -> int:
        pass #Nothing to do here, I can add a log if needed
    
    #Node:
    def _receiveParcel(self, parcel: Parcel) -> bool:
        if (parcel.type == Common.PARCEL_TYPE_NODE_STATE):
            content = parcel.content
            if (len(content) != 3):
                raise ValueError("State update content: " + str(content) + " not supported by mobile node")
            
            if (content[0] == self._edgeConnection.destNode()):
                self._edgeState = content[1:]
                if Logger.levelCanLog(3):
                    Logger.log("mobile id: " + str(self.id()) + " state update: " + str(self.fetchState(None)), 3)
            else:
                Logger.log("mobile node received a state update parcel from an edge which it is not connected to", 1)
        elif (parcel.type == Common.PARCEL_TYPE_TASK_RESULT):
            task = parcel.content
            task.powerConsumed += parcel.powerConsumed
            if (task.nodeId() != self.id()):
                raise ValueError("Mobile node (id: " + str(self.id()) +
                                 ") received task result belonging to another mobile node with id:" + str(task.nodeId()))
            self._taskCompleted(task)
        else:
            raise ValueError("Parcel type: " + str(parcel.type) + " not supported by mobile node")
    
    