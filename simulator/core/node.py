from abc import abstractmethod


class Node:
    def __init__(self) -> None:
        pass
    
    def setup(self, id: int) -> None:
        self._id = id
        
    def id(self) -> int:
        return self._id