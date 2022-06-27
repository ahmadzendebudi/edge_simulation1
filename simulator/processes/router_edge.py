from abc import abstractmethod
from typing import Dict, Sequence
from simulator.common import Common
from simulator.core.connection import Connection
from simulator.core.parcel import Parcel
from simulator.core.parcel_queue import ParcelQueue
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.processes.parcel_transmitter import ParcelTransmitter, ParcelTransmitterPlug
from simulator.processes import Package

class RouterEdgePlug:
    @abstractmethod
    def isNodeOfInterest(self, nodeId) -> bool:
        """It should retreive true if nodeId is a node we most send parcels to."""
        pass

    @abstractmethod
    def receiveRoutedParcel(self, parcel: Parcel):
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
        self._transmitterIdToDestNodeIdMap: Dict[int, int] = {}

    def updateConnections(self, mobileConnections: Sequence[Connection], edgeConnections: Sequence[Connection]):
        self._transmitterIdToDestNodeIdMap.clear()
        #update mobile connections:
        mobileUpdateSet = set(map(lambda connection: connection.destNode(), mobileConnections))
        mobileCurrentSet = set(self._mobileNodeMap.keys())
        dropSet = mobileCurrentSet.difference(mobileUpdateSet)
        for nodeId in dropSet:
            transmitter = self._mobileNodeMap[nodeId].transmitter
            #TODO we need to do something about the items in the corresponding transmission
            self._simulator.unregisterProcess(transmitter.id())
            del self._mobileNodeMap[nodeId]
        
        for connection in mobileConnections:
            nodeItem = self._mobileNodeMap.get(connection.destNode(), None)
            if nodeItem != None:
                nodeItem.connection = connection
                transmitter = nodeItem.transmitter
            else:
                transmitQueue = ParcelQueue()
                self._simulator.registerParcelQueue(transmitQueue)
                transmitter = ParcelTransmitter(self._simulator, transmitQueue, self)
                self._simulator.registerProcess(transmitter)
                self._mobileNodeMap[connection.destNode()] = NodeItem(connection, transmitter)
            
            self._transmitterIdToDestNodeIdMap[transmitter.id()] = connection.destNode()

        #update edge connections:
        edgeUpdateSet = set(map(lambda connection: connection.destNode(), edgeConnections))
        edgeCurrentSet = set(self._edgeNodeMap.keys())
        dropSet = edgeCurrentSet.difference(edgeUpdateSet)
        if len(dropSet) != 0:
            raise "Removing edge connections is not supported yet"
        
        for connection in edgeConnections:
            nodeItem = self._edgeNodeMap.get(connection.destNode(), None)
            if nodeItem != None:
                nodeItem.connection = connection
                transmitter = nodeItem.transmitter
            else:
                transmitQueue = ParcelQueue()
                self._simulator.registerParcelQueue(transmitQueue)
                transmitter = ParcelTransmitter(self._simulator, transmitQueue, self)
                self._simulator.registerProcess(transmitter)
                self._edgeNodeMap[connection.destNode()] = NodeItem(connection, transmitter)
            
            self._transmitterIdToDestNodeIdMap[transmitter.id()] = connection.destNode()
    

    def sendParcel(self, parcel: Parcel) -> Parcel:
        destId = parcel.destNodeId
        transmitter = self.getTransmitter(destId)
        if transmitter == None:
            #TODO check the routes if this parcel can be sent as package, otherwise halt the send for later
            pass
        else:
            transmitter.transmitQueue().put(parcel)
            self._simulator.registerEvent(Common.time(), transmitter.id())
        pass

    def _sendRoutedPackage(self, package: Parcel, nextHopId: int):
        transmitter = self.getTransmitter(nextHopId)
        if transmitter == None:
            raise "next hop is not a connection"
        transmitter.transmitQueue().put(package)
        self._simulator.registerEvent(Common.time(), transmitter.id())

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
            if package.destId == self._nodeId:
                self._plug.receiveRoutedParcel(parcel)
            elif len(package.route) > 0:
                nextHopId = package.route.pop()
                self._sendRoutedPackage(package, nextHopId)
            else:
                raise "package hops exhusted and we haven't reached destination node"
    
    def getAllConnections(self):
        return map(lambda nodeItem: nodeItem.connection, list(self._mobileNodeMap.values()) + list(self._edgeNodeMap.values()))

    def getEdgeConnections(self):
        return map(lambda nodeItem: nodeItem.connection, self._edgeNodeMap.values())
    
    def getMobileConnections(self):
        return map(lambda nodeItem: nodeItem.connection, self._mobileNodeMap.values())

    def getConnection(self, destId: int) -> Connection:
        nodeItem = self._getNodeItem(destId)
        if nodeItem == None:
            return None
        else:
            return nodeItem.connection

    def getConnectionByTransmitterId(self, transmitterId: int) -> Connection:
        destNodeId = self._transmitterIdToDestNodeIdMap[transmitterId]
        return self.getConnection(destNodeId)

    def getTransmitter(self, destId: int) -> ParcelTransmitter:
        nodeItem = self._getNodeItem(destId)
        if nodeItem == None:
            return None
        else:
            return nodeItem.transmitter

    def _getNodeItem(self, destId: int) -> NodeItem:
        nodeItem = self._mobileNodeMap.get(destId, None)
        if nodeItem == None:
            nodeItem = self._edgeNodeMap.get(destId, None)
        return nodeItem

    def fetchDestinationConnection(self, processId: int) -> Connection:
        return self.getConnectionByTransmitterId(processId)
    
    def parcelTransmissionComplete(self, parcel: Parcel, processId: int) -> int:
        pass#TODO how about you actually do the tensmission before calling this?

