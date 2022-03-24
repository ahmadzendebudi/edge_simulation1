class Node:
    def __init__(self, id: int) -> None:
        self._id = id
        
    def id(self) -> int:
        return self._id