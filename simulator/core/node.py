from abc import abstractmethod

from simulator.core.parcel import Parcel


class Node:
    def __init__(self) -> None:
        pass
    
    def setup(self, id: int) -> None:
        self._id = id
    
    @abstractmethod
    def _receiveParcel(self, parcel: Parcel) -> bool:
        """to be used only by simulator"""
        pass
        
    def id(self) -> int:
        return self._id