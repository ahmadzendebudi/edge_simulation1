class Parcel:
    def __init__(self, type: int, senderNodeId: int) -> None:
        """possible types are defined by the receiver node of the parcel"""
        self.type = type
        self.senderNodeId = senderNodeId