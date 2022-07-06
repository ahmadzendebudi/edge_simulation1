
import itertools
from typing import Callable, Dict, Sequence, Set, Tuple
import numpy as np
from simulator.config import Config
from simulator.core.connection import Connection
from simulator.core.simulator import Simulator
from simulator.core.task import Task
from simulator.environment.edge_node import EdgeNode, EdgeNodePlug
from simulator.environment.mobile_node import MobileNode, MobileNodePlug
from simulator.task_multiplexing.transition import Transition
from simulator.common import Common


class Device:
    def __init__(self, id, node, location=None) -> None:
        self.id = id
        self.node = node
        if location == None:
            self.location = self.getRandomLocation()
        else:
            self.location = location

    def getRandomLocation(self):
        return np.random.randint(1, 100, 2)


class MobileDevice(Device):
    def __init__(self, id, node, location=None, destLocation=None, time=0, velocity=None, edgeId=None) -> None:
        super().__init__(id, node, location)
        self.destLocation = destLocation
        self.time = time
        self.edgeId = edgeId
        if velocity == None:
            self.setRandomVelocity()
        else:
            self.velocity = velocity
        if destLocation == None:
            self.setRandomDestLocation()
        else:
            self.destLocation = destLocation

    def setRandomVelocity(self):
        a = Config.get("boxworld_mobile_velocity_min")
        b = Config.get("boxworld_mobile_velocity_max")
        self.velocity = (b - a) * np.random.random_sample() + a

    def setRandomDestLocation(self):
        self.destLocation = self.getRandomLocation()


class EdgeDevice(Device):
    def __init__(self, id, node, location, edgeIds: Set[int] = set(), mobileIds: Set[int] = set()) -> None:
        super().__init__(id, node, location)
        self.edgeIds = edgeIds
        self.mobileIds = mobileIds


class BoxWorldv2(EdgeNodePlug, MobileNodePlug):
    delay_coefficient = Config.get("delay_coefficient")
    power_coefficient = Config.get("power_coefficient")

    def build(self) -> Tuple[Sequence[EdgeNode], Sequence[MobileNode]]:
        self._loadConfig()
        edgeNodesLocation = [np.array([25, 25]), np.array(
            [75, 25]), np.array([75, 75]), np.array([25, 75])]

        self._edgeDevices: Dict[int, EdgeDevice] = {}
        self._mobileDevices: Dict[int, MobileDevice] = {}
        self._lastLocationUpdate = 0

        id = 0
        for location in edgeNodesLocation:
            id += 1
            flops = self._edge_cpu_core_tflops * (10 ** 12)
            cores = self._edge_cpu_cores
            device = EdgeDevice(id, EdgeNode(id, self, flops, cores), location)
            self._edgeDevices[id] = device

        mobileWattsPerTFlops = Config.get("mobile_watts_per_tflop")
        for _ in range(0, Config.get("boxworld_mobile_nodes")):
            id += 1
            flops = self._mobile_cpu_core_tflops * (10 ** 12)
            cores = self._mobile_cpu_cores
            mobileNode = MobileNode(id, self, flops, cores,
                                    metteredPowerConsumtionPerTFlops=mobileWattsPerTFlops)
            device = MobileDevice(id, mobileNode)
            self._mobileDevices[id] = device

        self.update_connections()

        return ([device.node for device in self._edgeDevices.values()],
                [device.node for device in self._mobileDevices.values()])

    def defaultRewards(self):
        edgeRewardFunction: Callable[[
            Transition], float] = lambda transition: - BoxWorldv2.delay_coefficient * transition.delay
        mobileRewardFunction: Callable[[Transition], float] = (lambda transition: - BoxWorldv2.delay_coefficient * transition.delay
                                                               - BoxWorldv2.power_coefficient * transition.powerConsumed)
        return (edgeRewardFunction, mobileRewardFunction)

    def _loadConfig(self):
        self._mobile_transmit_power_watts = Config.get(
            "mobile_transmit_power_watts")
        self._edge_transmit_power_watts = Config.get(
            "edge_transmit_power_watts")
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
        self._update_interval = Config.get("boxworld_update_interval")

    def update_locations(self, current_time):
        if self._lastLocationUpdate > current_time:
            raise "the locations are already updated beyond the given time, cannot go back in time!"
        elif self._lastLocationUpdate < current_time:
            for mobileDevice in self._mobileDevices.values():
                while mobileDevice.time < current_time:
                    distanceToDestination = self.distance(
                        mobileDevice.location, mobileDevice.destLocation)
                    arrivalTime = distanceToDestination / mobileDevice.velocity + mobileDevice.time
                    if arrivalTime > current_time:
                        alpha = (current_time - mobileDevice.time) / \
                            (arrivalTime - mobileDevice.time)
                        mobileDevice.location = (
                            1 - alpha) * mobileDevice.location + alpha * mobileDevice.destLocation
                        mobileDevice.time = current_time
                    else:
                        mobileDevice.location = mobileDevice.destLocation
                        mobileDevice.time = arrivalTime
                        mobileDevice.setRandomDestLocation()
                        mobileDevice.setRandomVelocity()
            self.update_connections()

    def update_connections(self):
        # updating edge-edge connections
        for edge1, edge2 in itertools.combinations(self._edgeDevices.values(), 2):
            if self.distance(edge1.location, edge2.location) < 80:
                edge1.edgeIds.add(edge2.id)
                edge2.edgeIds.add(edge1.id)

        # updating edge-mobile connections:
        for mobile in self._mobileDevices.values():
            closestEdge = None
            for edge in self._edgeDevices.values():
                if closestEdge == None or (self.distance(mobile.location, closestEdge.location) >
                                           self.distance(mobile.location, edge.location)):
                    closestEdge = edge
            if closestEdge == None:
                raise "no edge found for the mobile device to connect to"

            currentEdge = None if mobile.edgeId == None else self._edgeDevices[mobile.edgeId]
            if currentEdge == None or (self.distance(mobile.location, currentEdge.location) >
                                       self.distance(mobile.location, closestEdge.location) + 10):
                if currentEdge != None:
                    currentEdge.mobileIds.remove(mobile.id)
                closestEdge.mobileIds.add(mobile.id)
                mobile.edgeId = closestEdge.id

    def updateEdgeNodeConnections(self, nodeId: int, nodeExternalId: int) -> Tuple[Sequence[Connection], Sequence[Connection], int]:
        self.update_locations(Common.time())
        edgeConnections = []
        mobileConnections = []

        senderEdgeDevice = self._edgeDevices[nodeExternalId]
        for edgeDeviceId in senderEdgeDevice.edgeIds:
            receiverEdgeDevice = self._edgeDevices[edgeDeviceId]
            receiverEdgeNodeId = receiverEdgeDevice.node.id()
            # TODO modulation should be set properly
            datarate = self._sampleEdgeToEdgeDataRate(
                senderEdgeDevice, receiverEdgeDevice, 4)
            edgeConnections.append(Connection(
                nodeId, receiverEdgeNodeId, datarate))

        powerConsumption = Config.get("mobile_transmit_power_watts")
        for mobileDeviceId in senderEdgeDevice.mobileIds:
            receiverMobileDevice = self._mobileDevices[mobileDeviceId]
            receiverMobileNodeId = receiverMobileDevice.node.id()
            datarate = self._sampleEdgeToMobileDataRate(
                senderEdgeDevice, receiverMobileDevice, 100)  # TODO modulation should be set properly
            mobileConnections.append(Connection(
                nodeId, receiverMobileNodeId, datarate, powerConsumption))

        return (edgeConnections, mobileConnections, Common.time() + self._update_interval)

    def updateMobileNodeConnection(self, nodeId: int, nodeExternalId: int) -> Tuple[Connection, int]:
        self.update_locations(Common.time())
        mobileDevice = self._mobileDevices[nodeExternalId]
        edgeDevice = self._edgeDevices[mobileDevice.edgeId]
        datarate = self._sampleMobileToEdgeDataRate(
            mobileDevice, edgeDevice, 100)  # TODO modulation should be set properly
        powerConsumption = Config.get("mobile_transmit_power_watts")
        return (Connection(nodeId, edgeDevice["node"].id(), datarate, powerConsumption), Common.time() + self._update_interval)

    # TODO modulation should also be taken into account
    def _sampleEdgeToEdgeDataRate(self, transmtterDevice, receiverDevice, modulationChannels) -> int:
        return self._sampleDeviceToDeviceDataRate(transmtterDevice, self._edge_gain_dBi, self._edge_transmit_power_watts,
                                                  receiverDevice, self._edge_gain_dBi,
                                                  self._channel_frequency_GHz, self._channel_bandwidth_MHz, modulationChannels)

    # TODO modulation should also be taken into account
    def _sampleMobileToEdgeDataRate(self, mobileDevice, edgeDevice, modulationChannels) -> int:
        return self._sampleDeviceToDeviceDataRate(mobileDevice, self._mobile_gain_dBi, self._mobile_transmit_power_watts,
                                                  edgeDevice, self._edge_gain_dBi,
                                                  self._channel_frequency_GHz, self._channel_bandwidth_MHz, modulationChannels)

    # TODO modulation should also be taken into account
    def _sampleEdgeToMobileDataRate(self, edgeDevice, mobileDevice, modulationChannels) -> int:
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

        # 299792458 is the speed of light
        wavelength = 299792458/channelFrequency
        distance = self.distance(
            transmitterDevice["location"], receiverDevice["location"])

        receivePower = transmitPower * transmitGain * \
            receiveGain * (wavelength / (4 * np.pi * distance)) ** 2

        receiveNoisePower = 10 ** (self._gaussain_noise_dBm / 10)

        datarate = channelBandwidth * \
            np.log2(1 + receivePower / receiveNoisePower)
        datarate = int(datarate / modulationChannels)
        return datarate

    def distance(self, location1, location2) -> float:
        return np.sqrt(np.power(location1[0] - location2[0], 2) + np.power(location1[1] - location2[1], 2))
