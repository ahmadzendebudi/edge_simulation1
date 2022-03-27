
from typing import Sequence, Tuple
import numpy as np
from simulator.core.connection import Connection
from simulator.environment.edge_node import EdgeNode, EdgeNodePlug
from simulator.environment.mobile_node import MobileNode, MobileNodePlug

class BoxWorld(EdgeNodePlug, MobileNodePlug):
    def build(self) -> Tuple[Sequence[EdgeNode], Sequence[MobileNode]]:
        edgeNodesLocation = [[25, 25], [75, 25], [75, 75], [25, 75]]
        mobileNodesLocation = []
        for _ in range(100):
            mobileNodesLocation.append(np.random.randint(1, 100, 2).tolist())
        
        self._edgeDevices = {}
        self._mobileDevices = {}
        self._edgeNodes = []
        self._mobileNodes = []
        
        id = 0
        for location in edgeNodesLocation:
            id += 1
            device = {}
            device["id"] = id
            device["node"] = EdgeNode(id, self)
            device["location"] = location 
            self._edgeNodes.append(device["node"])
            self._edgeDevices[id] = device
            
        for location in mobileNodesLocation:
            id += 1
            device = {}
            device["id"] = id
            device["node"] = MobileNode(id, self)
            device["location"] = location 
            self._mobileNodes.append(device["node"])
            self._mobileDevices[id] = device
        
        self.setupConnections()
        
        return (self._edgeNodes, self._mobileNodes)
        
        
    
    def setupConnections(self):
        #mobile devices choose the closest edge to them
        #TODO if mobile devices move, the closest device should not only be closer to the current connection,
        #but also, the difference in distance should be higher than a number
        for mobileDevice in self._mobileDevices.values():
            closestEdge = None
            for edgeDevice in self._edgeDevices.values():
                if closestEdge == None:
                    closestEdge = edgeDevice
                elif (self.distance(mobileDevice["location"], closestEdge["location"]) > 
                      self.distance(mobileDevice["location"], edgeDevice["location"])):
                    closestEdge = edgeDevice
            if closestEdge != None:
                mobileDevice["connectionEdgeId"] = closestEdge["id"]
        
        
        #edge devices connect to mobile devices which are connected to them
        for edgeDevice in self._edgeDevices.values():
            edgeDevice["connectionsMobileId"] = []
            for mobileDevice in self._mobileDevices.values():
                if mobileDevice["connectionEdgeId"] == edgeDevice["id"]:
                    edgeDevice["connectionsMobileId"].append(mobileDevice["id"])
                    
        #edge devices connect to edge devices which are closer than a number
        for edgeDevice in self._edgeDevices.values():
            edgeDevice["connectionsEdgeId"] = []
            for otherDevice in self._edgeDevices.values():
                if (otherDevice["id"] != edgeDevice["id"] and 
                    self.distance(edgeDevice["location"], otherDevice["location"]) < 80):
                    edgeDevice["connectionsEdgeId"].append(otherDevice["id"])
                    
            
    def updateEdgeNodeConnections(self, nodeId: int, nodeExternalId: int) -> Tuple[Sequence[Connection], Sequence[Connection], int]:
        edgeConnections = []
        mobileConnections = []
        
        for edgeDeviceId in self._edgeDevices[nodeExternalId]["connectionsEdgeId"]:
            edgeDevice = self._edgeDevices[edgeDeviceId]
            edgeNodeId = edgeDevice["node"].id()
            #TODO bandwidth should be decided properly
            edgeConnections.append(Connection(nodeId, edgeNodeId, 10000))
        
        for mobileDeviceId in self._edgeDevices[nodeExternalId]["connectionsMobileId"]:
            mobileDevice = self._mobileDevices[mobileDeviceId]
            mobileNodeId = mobileDevice["node"].id()
            #TODO bandwidth should be decided properly
            mobileConnections.append(Connection(nodeId, mobileNodeId, 1000))
            
        return (edgeConnections, mobileConnections, None)
        
        
    def updateMobileNodeConnection(self, nodeId: int, nodeExternalId: int) -> Tuple[Connection, int]:
        edgeNodeId = self._mobileDevices[nodeExternalId]["connectionEdgeId"]
        #TODO bandwidth should be decided properly
        return (Connection(nodeId, edgeNodeId, 1000), None)
    
    def distance(self, location1: Sequence[int], location2: Sequence[int]) -> float:
        return np.sqrt(np.exp2(location1[0] - location2[0]) + np.exp2(location1[1] - location2[1]))
        
        
        