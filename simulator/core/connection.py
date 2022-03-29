class Connection:
    def __init__(self, sourceNode: int, destNode: int, datarate: int) -> None:
        self._sourceNode = sourceNode
        self._destNode = destNode
        self._datarate = datarate
        
    def destNode(self) -> int:
        return self._destNode
    
    def datarate(self) -> int:
        return self._datarate
    
    def id(self) -> int:
        return Connection.generateId(self._sourceNode, self._destNode)
    
    @classmethod
    def generateId(cls, sourceNodeId: int, destNodeId: int) -> int:
        return hash((sourceNodeId, destNodeId))