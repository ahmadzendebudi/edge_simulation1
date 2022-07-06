

from abc import abstractmethod
from typing import Sequence
import numpy as np
from simulator.common import Common
from simulator.core.connection import Connection
from simulator.core.parcel import Parcel
from simulator.core.parcel_queue import ParcelQueue
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator import Config

class ParcelTransmitterPlug:
    
    @abstractmethod
    def fetchDestinationConnection(self, processId: int) -> Connection:
        pass
    
    @abstractmethod
    def parcelTransmissionComplete(self, parcel: Parcel, processId: int) -> int:
        pass#TODO how about you actually do the tensmission before calling this?

class ParcelTransmitter(Process):
    def __init__(self, simulator: Simulator, queue: ParcelQueue, plug: ParcelTransmitterPlug) -> None:
        super().__init__()
        self._plug = plug
        self._liveParcel = None
        self._liveParcelCompletionTime = None
        self._liveParcelTransmitDuration = None
        self._simulator = simulator
        self._queue = queue
    
    def transmitQueue(self):
        return self._queue
        
    def wake(self) -> None:
        if (self._liveParcel != None and self._liveParcelCompletionTime <= Common.time()):
            destNodeId = self._plug.fetchDestinationConnection(self._id).destNode()
            self._liveParcel.powerConsumed += self._liveParcelPowerConsumtion
            self._simulator.sendParcel(self._liveParcel, destNodeId)
            self._plug.parcelTransmissionComplete(self._liveParcel, self._id)
            self._liveParcel = None
            self._liveParcelCompletionTime = None
            self._liveParcelTransmitDuration = None
        
        if (self._liveParcel is None):
            if self._queue.qsize() > 0:
                self._transmitParcel(self._queue.get())
        return super().wake()
    
    def _transmitParcel(self, Parcel: Parcel):
        self._liveParcel = Parcel
        connection = self._plug.fetchDestinationConnection(self._id)
        datarate = connection.datarate() * np.random.uniform(
            Config.get("connection_actual_datarate_low"), 
            Config.get("connection_actual_datarate_high"))
        self._liveParcelTransmitDuration = Parcel.size / datarate
        self._liveParcelCompletionTime = Common.time() + self._liveParcelTransmitDuration
        self._liveParcelPowerConsumtion = connection.metteredPowerConsumtion() * self._liveParcelTransmitDuration
        self._simulator.registerEvent(self._liveParcelCompletionTime, self._id)
        
    def remainingTransmitSize(self):
        remainingSize = 0
        connection = self._plug.fetchDestinationConnection(self._id)
        if (self._liveParcel != None and self._liveParcelCompletionTime <= Common.time()):
            remainingSize += ((Common.time() - self._liveParcelCompletionTime) /
                              self._liveParcelTransmitDuration) * self._liveParcel.size
        
        for parcel in self._queue.deque():
            remainingSize += parcel.size
            
        return remainingSize
    
    
    def remainingTransmitTaskWorkload(self):
        remainingWorkload = 0
        if (self._liveParcel != None and self._liveParcel.type == Common.PARCEL_TYPE_TASK
             and self._liveParcelCompletionTime <= Common.time()):
            remainingWorkload += self._liveParcel.content.workload()
        for parcel in self._queue.deque():
            if (parcel.type == Common.PARCEL_TYPE_TASK):
                remainingWorkload += parcel.content.workload()
            
        return remainingWorkload

    def allParcels(self) -> Sequence[Parcel]:
        parcels = list(self._queue.deque())
        if self._liveParcel != None:
            parcels.append(self._liveParcel)
        return parcels