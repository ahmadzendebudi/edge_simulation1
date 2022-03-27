from abc import abstractmethod
from simulator import Config

class LogOutput:
    @abstractmethod
    def receiveText(self, text: str):
        pass

class LogOutputConsolePrint(LogOutput):
    def receiveText(self, text: str):
        print(text)

class Logger:
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
            for logOutput in cls.logOutputs:
                logOutput.receiveText(text)
    
    @classmethod
    def levelCanLog(cls, level: int):
        if (level < 0):
            raise RuntimeError("level cannot be smaller than 0")
        
        if not hasattr(cls, "level"):
            cls.level = Config.get("debug_level")
        
        return level <= cls.level
    