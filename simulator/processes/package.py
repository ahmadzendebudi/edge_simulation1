import sys
from typing import Tuple
from simulator.core import Parcel

class Package:
    PACKAGE_TYPE_PAYLOAD = 0
    PACKAGE_TYPE_ROUTING = 1

    def __init__(self, type, originId, destId, packageId, route:Tuple[int], content:Parcel = None) -> None:
        self.type = type
        self.originId = originId
        self.destId = destId
        self.packageId = packageId
        self.content = content
        self.route = route

    def size(self):
        size = 24 + sys.getsizeof(self.route)
        if (self.content != None):
            size += self.content.size
        return size
    
    def __str__(self) -> str:
        return ("Package({type: " + str(self.type) + " originId: " + str(self.originId) + " destId: " +
                str(self.destId) + " packageId: " + str(self.packageId) + " content: " + 
                str(self.content) + " route: " + str(self.route) + "})")
    
class PackageTools:
    @classmethod
    def appendRoute(cls, package: Package, nodeId: int) -> Package:
        """Creates a new package and appends a new node id to the route member of the package"""
        return Package(package.type, package.originId, package.destId, package.packageId, package.route + (nodeId,), package.content)
    
    @classmethod
    def popRoute(cls, package: Package) -> Tuple[Package, int]:
        """Creates a new package and pops the right-most node id from the route member of the package
           It returns the new package and the poped node id"""
        nextHopId = package.route[len(package.route) - 1]
        return (Package(package.type, package.originId, package.destId, 
                package.packageId, package.route[:len(package.route) - 1], package.content), nextHopId)


