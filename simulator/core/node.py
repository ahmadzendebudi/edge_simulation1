from abc import abstractmethod

from simulator.core.parcel import Parcel
from simulator.core.parcel_queue import ParcelQueue
from simulator.core.process import Process


class Node(Process):
    def __init__(self, externalId: int) -> None:
        self._externalId = externalId
    
    def setup(self, id: int) -> None:
        self._id = id
        self._parcelQueue = ParcelQueue()
    
    def parcelInbox(self, parcel: Parcel):
        self._parcelQueue.put(parcel)
        
    def wake(self) -> None:
        while self._parcelQueue.qsize() > 0:
            self._receiveParcel(self._parcelQueue.get())
    
    @abstractmethod
    def _receiveParcel(self, parcel: Parcel) -> bool:
        """to be called only by simulator, should not be called directly"""
        pass
        
    def id(self) -> int:
        return self._id
        
    def externalId(self) -> int:
        return self._externalId