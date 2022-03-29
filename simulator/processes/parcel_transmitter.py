
from abc import abstractmethod
from simulator.common import Common
from simulator.core.connection import Connection
from simulator.core.parcel import Parcel
from simulator.core.parcel_queue import ParcelQueue
from simulator.core.process import Process
from simulator.core.simulator import Simulator

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
        self._simulator = simulator
        self._queue = queue
    
    def transmitQueue(self):
        return self._queue
        
    def wake(self) -> None:
        if (self._liveParcel != None and self._liveParcelCompletionTime <= Common.time()):
            destNodeId = self._plug.fetchDestinationConnection(self._id).destNode()
            self._simulator.sendParcel(self._liveParcel, destNodeId)
            self._plug.parcelTransmissionComplete(self._liveParcel, self._id)
            self._liveParcel = None
            self._liveParcelCompletionTime = None
        
        if (self._liveParcel == None):
            if self._queue.qsize() > 0:
                self._transmitParcel(self._queue.get())
        return super().wake()
    
    def _transmitParcel(self, Parcel: Parcel):
        self._liveParcel = Parcel
        connection = self._plug.fetchDestinationConnection(self._id)
        self._liveParcelCompletionTime = Common.time() + Parcel.size / connection.datarate()
        self._simulator.registerEvent(self._liveParcelCompletionTime, self._id)