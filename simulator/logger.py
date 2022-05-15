from abc import abstractmethod
from simulator import Config
from simulator.common import Common

class LogOutput:
    @abstractmethod
    def receiveText(self, text: str, time: int):
        pass
    
    @abstractmethod
    def close(self):
        pass

class LogOutputConsolePrint(LogOutput):
    def receiveText(self, text: str, time: int):
        print("Time: " + str(time) + ", " + text)
    
    def close(self):
        return super().close()

class LogOutputTextFile(LogOutput):
    def __init__(self, location: str) -> None:
        super().__init__()
        self.file = open(location, "a")
        self.file.truncate(0)

    def receiveText(self, text: str, time: int):
        self.file.write("Time: " + str(time) + ", " + text + "\n")
    
    def close(self):
        self.file.close()
    
class Logger:
    
    @classmethod
    def unregisterAllOutPut(cls) -> None:
        cls.logOutputs = []
    
    @classmethod
    def registerLogOutput(cls, output: LogOutput) -> None:
        if not hasattr(cls, "logOutputs"):
            cls.logOutputs = []
        cls.logOutputs.append(output)
    
    @classmethod
    def log(cls, text: str, level: int) -> None:
        if (level < 0):
            raise RuntimeError("level cannot be smaller than 0")
        
        if not hasattr(cls, "level"):
            cls.level = Config.get("debug_level")
        
        if (level <= cls.level):
            time = Common.time()
            for logOutput in cls.logOutputs:
                logOutput.receiveText(text, time)
    
    @classmethod
    def levelCanLog(cls, level: int):
        if (level < 0):
            raise RuntimeError("level cannot be smaller than 0")
        
        if not hasattr(cls, "level"):
            cls.level = Config.get("debug_level")
        
        return level <= cls.level
    
    @classmethod
    def closeLogOutputs(cls):
        if hasattr(cls, "logOutputs"):
            for logOutput in cls.logOutputs:
                logOutput.close()
                
    