class Parcel:
    def __init__(self, type: int, size: int, content, senderNodeId: int, destNodeId: int) -> None:
        """possible types are defined in the common module"""
        self.type = type
        self.content = content
        self.senderNodeId = senderNodeId
        self.destNodeId = destNodeId
        self.size = size
        self.powerConsumed = 0