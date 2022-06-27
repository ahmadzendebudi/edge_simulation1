from abc import abstractmethod
from typing import Dict, Sequence
from simulator.common import Common
from simulator.core.connection import Connection
from simulator.core.parcel import Parcel
from simulator.core.parcel_queue import ParcelQueue
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.processes.parcel_transmitter import ParcelTransmitter, ParcelTransmitterPlug

class Package:
    PACKAGE_TYPE_PAYLOAD = 0
    PACKAGE_TYPE_ROUTING = 1

    def __init__(self, type, originId, destId, packageId, route:Sequence[int], content:Parcel = None) -> None:
        self.type = type
        self.originId = originId
        self.destId = destId
        self.packageId = packageId
        self.content = content
        self.route = route

class RouterEdgePlug:
    @abstractmethod
    def isNodeOfInterest(self, nodeId) -> bool:
        """It should retreive true if nodeId is a node we most send parcels to."""
        pass

    @abstractmethod
    def sendRoutedParcel(self, parcel: Parcel, destId: int):
        pass

class NodeItem:
    def __init__(self, connection: Connection, transmitter: ParcelTransmitter) -> None:
        self.connection = connection
        self.transmitter = transmitter

class RouterEdge(Process, ParcelTransmitterPlug):  
    def __init__(self, simulator: Simulator, nodeId: int, plug: RouterEdgePlug) -> None:
        self._nodeId = nodeId
        self._plug = plug
        self._simulator = simulator
        self._routeMap = {}
        self._mobileNodeMap: Dict[int, NodeItem] = {}
        self._edgeNodeMap: Dict[int, NodeItem] = {}

    def updateConnections(self, mobileConnections: Sequence[Connection], edgeConnections: Sequence[Connection]):
        #update mobile connections:
        mobileUpdateSet = set(map(lambda connection: connection.destNode(), mobileConnections))
        mobileCurrentSet = set(self._mobileNodeMap.keys())
        dropSet = mobileCurrentSet.difference(mobileUpdateSet)
        for nodeId in dropSet:
            transmitter = self._mobileNodeMap[nodeId].transmitter
            #TODO we need to do something about the items in the corresponding transmission
            self._simulator.unregisterProcess(transmitter.id())
            del self._mobileNodeMap[nodeId]
        pass
        for connection in mobileConnections:
            nodeItem = self._mobileNodeMap.get(connection.destNode(), None)
            if nodeItem != None:
                nodeItem.connection = connection
            else:
                transmitQueue = ParcelQueue()
                self._simulator.registerParcelQueue(transmitQueue)
                transmitter = ParcelTransmitter(self._simulator, transmitQueue, self)
                self._simulator.registerProcess(transmitter)
                self._mobileNodeMap[connection.destNode()] = NodeItem(connection, transmitter)

        #update edge connections:
        edgeUpdateSet = set(map(lambda connection: connection.destNode(), edgeConnections))
        edgeCurrentSet = set(self._edgeNodeMap.keys())
        if edgeCurrentSet != edgeUpdateSet:
            raise "Changing edge connections is not supported yet"        
        for connection in edgeConnections:
            nodeItem = self._edgeNodeMap[connection.destNode()]
            nodeItem.connection = connection


    def sendParcel(self, parcel: Parcel) -> Parcel:
        destId = parcel.destNodeId
        nodeItem = self._mobileNodeMap.get(destId, None)
        if nodeItem == None:
            #TODO check the routes if this parcel can be sent as package, otherwise halt the send for later
            pass
        else:
            nodeItem.transmitter.transmitQueue().put(parcel)
            self._simulator.registerEvent(Common.time(), nodeItem.transmitter.id())
        pass

    def receivePackage(self, parcel: Parcel) -> int:
        if parcel.type != Common.PARCEL_TYPE_PACKAGE:
            raise "parcel is not a package"
        package: Package = parcel.content
        if package.type == Package.PACKAGE_TYPE_ROUTING:
            #TODO check to see if a package with the same id and nodeid has already been received
            if self._plug.isNodeOfInterest(package.originId):
                self._routeMap[package.originId] = package.route
            #TODO send the package to all neighboring edges after adding this node id to route
        elif package.type == Package.PACKAGE_TYPE_PAYLOAD:
            pass

    def getTransmitter(self, destId: int) -> ParcelTransmitter:
        transmitter = self._mobileNodeMap.get(destId, None)
        if transmitter == None:
            transmitter = self._edgeNodeMap.get(destId, None)
        return transmitter
        
    def fetchDestinationConnection(self, processId: int) -> Connection:
        pass
    
    def parcelTransmissionComplete(self, parcel: Parcel, processId: int) -> int:
        pass#TODO how about you actually do the tensmission before calling this?
