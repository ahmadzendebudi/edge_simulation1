class Parcel:
    def __init__(self, type: int, size: int, content, senderNodeId: int, workload: int = 0) -> None:
        """possible types are defined in the common module"""
        self.type = type
        self.senderNodeId = senderNodeId
        self.content = content
        self.size = size
        self.workload = workload
        self.powerConsumed = 0