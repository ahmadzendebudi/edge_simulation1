
from typing import Sequence, Tuple
import numpy as np
from simulator.config import Config
from simulator.core.connection import Connection
from simulator.environment.edge_node import EdgeNode, EdgeNodePlug
from simulator.environment.mobile_node import MobileNode, MobileNodePlug

class BoxWorld(EdgeNodePlug, MobileNodePlug):
    def build(self) -> Tuple[Sequence[EdgeNode], Sequence[MobileNode]]:
        self._loadConfig()
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
            flops = self._edge_cpu_core_tflops * (10 ** 12)
            cores = self._edge_cpu_cores
            device["node"] = EdgeNode(id, self, flops, cores)
            device["location"] = location 
            self._edgeNodes.append(device["node"])
            self._edgeDevices[id] = device
            
        for location in mobileNodesLocation:
            id += 1
            device = {}
            device["id"] = id
            flops = self._mobile_cpu_core_tflops * (10 ** 12)
            cores = self._mobile_cpu_cores
            device["node"] = MobileNode(id, self, flops, cores)
            device["location"] = location 
            self._mobileNodes.append(device["node"])
            self._mobileDevices[id] = device
        
        self.setupConnections()
        
        return (self._edgeNodes, self._mobileNodes)
        
    def _loadConfig(self):
        self._mobile_transmit_power_watts = Config.get("mobile_transmit_power_watts")
        self._edge_transmit_power_watts = Config.get("edge_transmit_power_watts")
        self._mobile_gain_dBi = Config.get("mobile_gain_dBi")
        self._edge_gain_dBi = Config.get("edge_gain_dBi")
        self._channel_frequency_GHz = Config.get("channel_frequency_GHz")
        self._channel_bandwidth_MHz = Config.get("channel_bandwidth_MHz")
        self._gaussain_noise_dBm = Config.get("gaussain_noise_dBm")
        self._gaussain_noise_sd_dBm = Config.get("gaussain_noise_sd_dBm")
        self._task_size_kBit = Config.get("task_size_kBit")
        self._task_size_sd_kBit = Config.get("task_size_sd_kBit")
        self._task_size_min_kBit = Config.get("task_size_min_kBit")
        self._task_kflops_per_bit = Config.get("task_kflops_per_bit")
        self._task_kflops_per_bit_sd = Config.get("task_kflops_per_bit_sd")
        self._task_kflops_per_bit_min = Config.get("task_kflops_per_bit_min")
        self._mobile_cpu_core_tflops = Config.get("mobile_cpu_core_tflops")
        self._mobile_cpu_cores = Config.get("mobile_cpu_cores")
        self._edge_cpu_core_tflops = Config.get("edge_cpu_core_tflops")
        self._edge_cpu_cores = Config.get("edge_cpu_cores")
    
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
        
        senderEdgeDevice = self._edgeDevices[nodeExternalId]
        for edgeDeviceId in senderEdgeDevice["connectionsEdgeId"]:
            receiverEdgeDevice = self._edgeDevices[edgeDeviceId]
            receiverEdgeNodeId = receiverEdgeDevice["node"].id()
            datarate = self._sampleEdgeToEdgeDataRate(senderEdgeDevice, receiverEdgeDevice, 4)#TODO modulation should be set properly
            edgeConnections.append(Connection(nodeId, receiverEdgeNodeId, datarate))
        
        for mobileDeviceId in senderEdgeDevice["connectionsMobileId"]:
            receiverMobileDevice = self._mobileDevices[mobileDeviceId]
            receiverMobileNodeId = receiverMobileDevice["node"].id()
            datarate = self._sampleEdgeToMobileDataRate(senderEdgeDevice, receiverMobileDevice, 100)#TODO modulation should be set properly
            mobileConnections.append(Connection(nodeId, receiverMobileNodeId, datarate))
            
        return (edgeConnections, mobileConnections, None)
        
        
    def updateMobileNodeConnection(self, nodeId: int, nodeExternalId: int) -> Tuple[Connection, int]:
        mobileDevice = self._mobileDevices[nodeExternalId]
        edgeDeviceId = mobileDevice["connectionEdgeId"]
        edgeDevice = self._edgeDevices[edgeDeviceId]
        datarate = self._sampleMobileToEdgeDataRate(mobileDevice, edgeDevice, 100)#TODO modulation should be set properly
        return (Connection(nodeId, edgeDevice["node"].id(), datarate), None)
    
    def _sampleEdgeToEdgeDataRate(self, transmtterDevice, receiverDevice, modulationChannels) -> int: #TODO modulation should also be taken into account 
        return self._sampleDeviceToDeviceDataRate(transmtterDevice, self._edge_gain_dBi, self._edge_transmit_power_watts,
                                             receiverDevice, self._edge_gain_dBi,
                                             self._channel_frequency_GHz, self._channel_bandwidth_MHz, modulationChannels)
    
    def _sampleMobileToEdgeDataRate(self, mobileDevice, edgeDevice, modulationChannels) -> int: #TODO modulation should also be taken into account 
        return self._sampleDeviceToDeviceDataRate(mobileDevice, self._mobile_gain_dBi, self._mobile_transmit_power_watts,
                                             edgeDevice, self._edge_gain_dBi,
                                             self._channel_frequency_GHz, self._channel_bandwidth_MHz, modulationChannels)
    
    def _sampleEdgeToMobileDataRate(self, edgeDevice, mobileDevice, modulationChannels) -> int: #TODO modulation should also be taken into account 
        return self._sampleDeviceToDeviceDataRate(edgeDevice, self._edge_gain_dBi, self._edge_transmit_power_watts,
                                             mobileDevice, self._mobile_gain_dBi,
                                             self._channel_frequency_GHz, self._channel_bandwidth_MHz, modulationChannels)
        
    def _sampleDeviceToDeviceDataRate(self, transmitterDevice, transmitGain_dBi, transmitPower,
                                      receiverDevice, receiveGain_dBi,
                                      channelFrequency_GHz, channelBandwidth_MHz, modulationChannels):
        transmitGain = 10 ** (transmitGain_dBi / 10)
        receiveGain = 10 ** (receiveGain_dBi / 10)
        channelFrequency = channelFrequency_GHz * 10 ** 9
        channelBandwidth = channelBandwidth_MHz * 10 ** 6
        
        #299792458 is the speed of light
        wavelength = 299792458/channelFrequency
        distance = self.distance(transmitterDevice["location"], receiverDevice["location"])
        
        receivePower = transmitPower * transmitGain * receiveGain * (wavelength / (4 * np.pi * distance)) ** 2
        
        receiveNoisePower = 10 ** (self._gaussain_noise_dBm / 10)
        
        datarate = channelBandwidth * np.log2(1 + receivePower / receiveNoisePower)
        datarate = int(datarate / modulationChannels)
        return datarate  
    
    def distance(self, location1: Sequence[int], location2: Sequence[int]) -> float:
        return np.sqrt(np.power(location1[0] - location2[0], 2) + np.power(location1[1] - location2[1], 2))
        
        
        