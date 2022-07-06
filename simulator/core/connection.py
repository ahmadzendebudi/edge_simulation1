class Connection:
    def __init__(self, sourceNode: int, destNode: int, datarate: int, metteredPowerConsumtion: float = 0) -> None:
        self._sourceNode = sourceNode
        self._destNode = destNode
        self._datarate = datarate
        self._metteredPowerConsumtion = metteredPowerConsumtion
        
    def destNode(self) -> int:
        return self._destNode
    
    def datarate(self) -> int:
        return self._datarate
    
    def id(self) -> int:
        return Connection.generateId(self._sourceNode, self._destNode)
    
    def metteredPowerConsumtion(self) -> float:
        return self._metteredPowerConsumtion
    
    def __str__(self) -> str:
        return ("Connection({" + "_sourceNode:" + str(self._sourceNode) + " _destNode:" + str(self._destNode) +
                " _datarate:" + str(self._datarate) + " _metteredPowerConsumtion:" + str(self._metteredPowerConsumtion) + "})")

    @classmethod
    def generateId(cls, sourceNodeId: int, destNodeId: int) -> int:
        return hash((sourceNodeId, destNodeId))

