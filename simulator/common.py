import simulator

class Common:
    PARCEL_TYPE_TASK = "parcelTypeTask"
    PARCEL_TYPE_TASK_RESULT = "parcelTypeTaskResult"
    PARCEL_TYPE_NODE_STATE = "parcelTypeNodeState"
    
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