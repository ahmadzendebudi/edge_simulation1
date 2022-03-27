class Connection:
    def __init__(self, sourceNode: int, destNode: int, bandwidth: int) -> None:
        self._sourceNode = sourceNode
        self._destNode = destNode
        self._bandwidth = bandwidth
        
    def destNode(self) -> int:
        return self._destNode
    
    def bandwidth(self) -> int:
        return self._bandwidth
    
    def id(self) -> int:
        return Connection.generateId(self._sourceNode, self._destNode)
    
    @classmethod
    def generateId(cls, sourceNodeId: int, destNodeId: int) -> int:
        return hash((sourceNodeId, destNodeId))