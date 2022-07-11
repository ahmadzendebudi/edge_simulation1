from abc import abstractmethod
from imp import is_frozen_package
from typing import Dict, List, Sequence, Tuple
from simulator.common import Common
from simulator.config import Config
from simulator.logger import Logger
from simulator.core.connection import Connection
from simulator.core.parcel import Parcel
from simulator.core.parcel_queue import ParcelQueue
from simulator.core.process import Process
from simulator.core.simulator import Simulator
from simulator.processes.package import PackageTools
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
class RouteItem:
    def __init__(self, route: Tuple[int], update_time: int) -> None:
        self.route = route
        self.update_time = update_time

class RouterEdge(Process, ParcelTransmitterPlug):  
    def __init__(self, simulator: Simulator, nodeId: int, plug: RouterEdgePlug) -> None:
        self._nodeId = nodeId
        self._plug = plug
        self._simulator = simulator
        self._routeMap: Dict[int, RouteItem] = {}
        self._mobileNodeMap: Dict[int, NodeItem] = {}
        self._edgeNodeMap: Dict[int, NodeItem] = {}
        self._transmitterIdToDestNodeIdMap: Dict[int, int] = {}
        self._routeBroadcast = []
        self._waitingParcels: List[Parcel] = []

        self.ROUTER_UPDATE_TIMEOUT = Config.get("router_route_update_time_out")

    def updateConnections(self, mobileConnections: Sequence[Connection], edgeConnections: Sequence[Connection]):
        self._transmitterIdToDestNodeIdMap.clear()
        #update mobile connections:
        mobileUpdateSet = set(map(lambda connection: connection.destNode(), mobileConnections))
        mobileCurrentSet = set(self._mobileNodeMap.keys())
        dropSet = mobileCurrentSet.difference(mobileUpdateSet)
        for nodeId in dropSet:
            transmitter = self._mobileNodeMap[nodeId].transmitter
            self._waitingParcels += transmitter.allParcels()
            self._simulator.unregisterProcess(transmitter.id())
            self._simulator.unregisterParcelQueue(transmitter._queue.id())
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
        #we should examine the waiting parcels after all connections are updated
        self._removeInvalidRoutes()
        self._resendWaitingParcels()

    def sendParcel(self, parcel: Parcel) -> Parcel:
        destId = parcel.destNodeId
        transmitter = self.getTransmitter(destId)
        if transmitter is None and parcel.hops > 1:
            if parcel.type == Common.PARCEL_TYPE_PACKAGE:
                Logger.log("!!WARNING!! A package is being repackaged, is it intentional? | " + str(parcel), 1)
            routeItem: RouteItem = self._routeMap.get(parcel.destNodeId, None)
            if routeItem is None:
                self._waitingParcels.append(parcel)
            elif len(routeItem.route) <= parcel.hops:
                route = routeItem.route
                parcel.hops -= len(route)
                package_route = route[:len(route) - 1]
                nextHop = route[len(route) - 1]
                package = Package(Package.PACKAGE_TYPE_PAYLOAD, parcel.senderNodeId, parcel.destNodeId, 
                                  self._getSequentialId(), package_route, parcel)
                forwardParcel = Parcel(Common.PARCEL_TYPE_PACKAGE, package.size(), package, self._nodeId, nextHop)
                self.sendParcel(forwardParcel)
        elif not transmitter is None:
            transmitter.transmitQueue().put(parcel)
            self._simulator.registerEvent(Common.time(), transmitter.id())

    def receivePackage(self, parcel: Parcel) -> int:
        if parcel.type != Common.PARCEL_TYPE_PACKAGE:
            raise RuntimeError("parcel is not a package")
        package: Package = parcel.content
        if package.type == Package.PACKAGE_TYPE_ROUTING:
            duplicatePackage = self._isDuplicateRouteBroadcast(package.originId, package.packageId)
            if not duplicatePackage:
                if not package.originId in self._mobileNodeMap:
                    if len(package.route) < 2:
                        raise RuntimeError("route length is smaller than 2, route is impossible")
                    self._routeMap[package.originId] = RouteItem(package.route, Common.time())
                if self._hasWaitingParcel(package.originId):
                    self._resendWaitingParcels()
                forwardPackage = PackageTools.appendRoute(package, self._nodeId)
                for connection in self.getEdgeConnections():
                    if connection.destNode() != parcel.senderNodeId:
                        forwardParcel = Parcel(Common.PARCEL_TYPE_PACKAGE, forwardPackage.size(),
                                              forwardPackage, self._nodeId, connection.destNode())
                        self.sendParcel(forwardParcel)
        elif package.type == Package.PACKAGE_TYPE_PAYLOAD:
            if package.destId == self._nodeId:
                self._plug.receiveRoutedParcel(package.content)
            elif len(package.route) > 0:
                #print("package route before forwarding:" + str(package.route))#TODO remove
                newPackage, nextHopId = PackageTools.popRoute(package)
                parcel = Parcel(Common.PARCEL_TYPE_PACKAGE, newPackage.size(), newPackage, self._nodeId, nextHopId)
                self.sendParcel(parcel)
            else:
                raise RuntimeError("package hops exhusted and we haven't reached destination node")
    
    def getAllConnections(self):
        return map(lambda nodeItem: nodeItem.connection, list(self._mobileNodeMap.values()) + list(self._edgeNodeMap.values()))

    def getEdgeConnections(self):
        return map(lambda nodeItem: nodeItem.connection, self._edgeNodeMap.values())
    
    def getMobileConnections(self):
        return map(lambda nodeItem: nodeItem.connection, self._mobileNodeMap.values())

    def getConnection(self, destId: int) -> Connection:
        nodeItem = self._getNodeItem(destId)
        if nodeItem is None:
            return None
        else:
            return nodeItem.connection

    def getConnectionByTransmitterId(self, transmitterId: int) -> Connection:
        destNodeId = self._transmitterIdToDestNodeIdMap[transmitterId]
        return self.getConnection(destNodeId)

    def getTransmitter(self, destId: int) -> ParcelTransmitter:
        nodeItem = self._getNodeItem(destId)
        if nodeItem is None:
            return None
        else:
            return nodeItem.transmitter

    def _getNodeItem(self, destId: int) -> NodeItem:
        nodeItem = self._mobileNodeMap.get(destId, None)
        if nodeItem is None:
            nodeItem = self._edgeNodeMap.get(destId, None)
        return nodeItem

    def _isDuplicateRouteBroadcast(self, originId: int, packageId: int) -> bool:
        lifespan = Config.get("router_route_broadcast_record_lifespan")
        self._routeBroadcast = [x for x in self._routeBroadcast if x[2] > Common.time() - lifespan]
        duplicateRoutBroadcast = any(map(lambda item: item[0] == originId and item[1] == packageId, self._routeBroadcast))
        if not duplicateRoutBroadcast:
            self._routeBroadcast.append((originId, packageId, Common.time()))
        return duplicateRoutBroadcast

    def _resendWaitingParcels(self):
        oldWaitingParcels = tuple(self._waitingParcels)
        self._waitingParcels.clear()
        for parcel in oldWaitingParcels:
            self.sendParcel(parcel)

    def _removeInvalidRoutes(self):
        droplist = []
        for nodeId, route in self._routeMap.items():
            keepRoute = self.getConnection(nodeId) == None# and (self._plug.isNodeOfInterest(nodeId) or
            #    self._hasWaitingParcel(nodeId) or route.update_time + self.ROUTER_UPDATE_TIMEOUT > Common.time())
            if not keepRoute:
                droplist.append(nodeId)
        for id in droplist:
            self._routeMap.pop(id, None)

    def _hasWaitingParcel(self, destId: int) -> bool:
        return any(map(lambda parcel: parcel.destNodeId == destId, self._waitingParcels))

    def fetchDestinationConnection(self, processId: int) -> Connection:
        return self.getConnectionByTransmitterId(processId)
    
    def parcelTransmissionComplete(self, parcel: Parcel, processId: int) -> int:
        pass#TODO how about you actually do the tensmission before calling this?
    
    
    def _getSequentialId(self):
        if not hasattr(self, "_lastSequentialId"):
            self._lastSequentialId = 0
        self._lastSequentialId += 1
        return self._lastSequentialId
