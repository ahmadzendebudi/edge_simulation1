class Common:
    @classmethod
    def time(cls) -> int:
        if not hasattr(cls, "_time"):
            raise RuntimeError("time is still not set by the simulator, time should not be referenced before the simulator is created")
        return cls._time
    
    def setTime(cls, time: int):
        cls._time = time