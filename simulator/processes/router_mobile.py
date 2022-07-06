from abc import abstractmethod
from simulator.common import Common
from simulator.core import Process
from simulator.core.connection import Connection
from simulator.core.parcel import Parcel
from simulator.core.parcel_queue import ParcelQueue
from simulator.core.simulator import Simulator
from simulator.processes.package import Package
from simulator.processes.parcel_transmitter import ParcelTransmitter, ParcelTransmitterPlug
class RouterMobilePlug:
    @abstractmethod
    def receiveRoutedParcel(self, parcel: Parcel):
        pass

class RouterMobile(Process, ParcelTransmitterPlug):
    def __init__(self, simulator: Simulator, nodeId: int, plug: RouterMobilePlug) -> None:
        self._nodeId = nodeId
        self._simulator = simulator
        self._plug = plug
        self._connection = None
        self._transmitter = None
    def updateConnection(self, mobileConnection: Connection):
        if self._connection != None and self._connection.destNode() != mobileConnection.destNode():
            package = Package(Package.PACKAGE_TYPE_ROUTING, self._nodeId, None, self._getSequentialId(), (self._nodeId,))
            parcel = Parcel(Common.PARCEL_TYPE_PACKAGE, package.size(), package, self._nodeId, self._connection.destNode())
            self.sendParcel(parcel)
            #TODO current transmission can either continue or cancel and restart with this new edge
        self._connection = mobileConnection
        if self._transmitter is None:
            transmitQueue = ParcelQueue()
            self._simulator.registerParcelQueue(transmitQueue)
            self._transmitter = ParcelTransmitter(self._simulator, transmitQueue, self)
            self._simulator.registerProcess(self._transmitter)
    
    def sendParcel(self, parcel: Parcel) -> Parcel:
        if self._transmitter is None:
            raise "mobile node not connected to an edge device"
        elif self._connection.destNode() != parcel.destNodeId:
            raise "parcel has a different destNodeId than the mobile node edge connection"
        else:
            self._transmitter.transmitQueue().put(parcel)
            self._simulator.registerEvent(Common.time(), self._transmitter.id())

    def receivePackage(self, parcel: Parcel) -> int:
        if parcel.type != Common.PARCEL_TYPE_PACKAGE:
            raise "parcel is not a package"
        package: Package = parcel.content
        if package.type == Package.PACKAGE_TYPE_ROUTING:
            #Discard, mobile nodes do not need to route packages
            pass
        elif package.type == Package.PACKAGE_TYPE_PAYLOAD:
            if package.destId != self._nodeId:
                raise "mobile node received a package not meant for it"
            parcel: Parcel = package.content
            self._plug.receiveRoutedParcel(parcel)


    def getTransmitter(self):
        return self._transmitter
    
    def getConnection(self):
        return self._connection
        
    def fetchDestinationConnection(self, processId: int) -> Connection:
        return self._connection
    
    def parcelTransmissionComplete(self, parcel: Parcel, processId: int) -> int:
        pass #Nothing to do here, I can add a log if needed

    
    def _getSequentialId(self):
        if not hasattr(self, "_lastSequentialId"):
            self._lastSequentialId = 0
        self._lastSequentialId += 1
        return self._lastSequentialId
