from typing import Deque
from simulator.core import Parcel

class Package:
    PACKAGE_TYPE_PAYLOAD = 0
    PACKAGE_TYPE_ROUTING = 1

    def __init__(self, type, originId, destId, packageId, route:Deque[int], content:Parcel = None) -> None:
        self.type = type
        self.originId = originId
        self.destId = destId
        self.packageId = packageId
        self.content = content
        self.route = route
