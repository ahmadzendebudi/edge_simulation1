from typing import Tuple


class Parcel:
    def __init__(self, type: int, size: int, content, senderNodeId: int, destNodeId: int, hops = 32) -> None:
        """possible types are defined in the common module"""
        self.type = type
        self.content = content
        self.senderNodeId = senderNodeId
        self.destNodeId = destNodeId
        self.size = size
        self.powerConsumed = 0
        self.hops = hops
    
    def __str__(self) -> str:
        return ("Parcel({" + "type: " + str(self.type) + " content: " + str(self.content) +
        " senderNodeId: " + str(self.senderNodeId) + " destNodeId: " + str(self.destNodeId) + 
        " size: " + str(self.size) + " powerConsumed: " + str(self.powerConsumed) +"})")