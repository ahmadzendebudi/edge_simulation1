import time
import simulator

class Common:
    PARCEL_TYPE_TASK = "parcelTypeTask"
    PARCEL_TYPE_TASK_RESULT = "parcelTypeTaskResult"
    PARCEL_TYPE_NODE_STATE = "parcelTypeNodeState"
    PARCEL_TYPE_TRANSITION = "parcelTypeTransition"
    PARCEL_TYPE_EDGE_TRANSITION = "parcelTypeEdgeTransition"
    PARCEL_TYPE_ANN_PARAMS = "parcelTypeAnnParams"
    PARCEL_TYPE_PACKAGE = "parcelTypePackage"
    
    @classmethod
    def time(cls) -> float:
        if not hasattr(cls, "_time"):
            raise RuntimeError("time is still not set by the simulator, time should not be referenced before the simulator is created")
        return cls._time
    
    @classmethod
    def setTime(cls, time: float):
        cls._time = time
        
    @classmethod
    def generateUniqueId(cls):
        if not hasattr(cls, "_lastId"):
            cls._lastId = simulator.Config.get("initial_unique_id")
        else:
            cls._lastId += 1
        return cls._lastId
    
    @classmethod
    def setSimulationRunId(cls, id: str):
        cls._simulationRunId = id
    
    @classmethod
    def simulationRunId(cls):
        if not hasattr(cls, "_simulationRunId"):
            cls._simulationRunId = hex(hash(time.time()))
        return cls._simulationRunId
    
    @classmethod
    def simulationResetRunId(cls):
        cls._simulationRunId = hex(hash(time.time()))
        return cls._simulationRunId