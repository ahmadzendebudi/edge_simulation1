class Connection:
    def __init__(self, destNode: int, bandwidth: int) -> None:
        self._destNode = destNode
        self._bandwidth = bandwidth
        
    def destNode(self):
        return self._destNode
    
    def bandwidth(self):
        return self._bandwidth