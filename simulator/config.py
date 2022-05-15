import json

class Config:
    
    @classmethod
    def _initConfig(cls):
        with open("simulator/config.json", "r") as read_file:
            cls._conf = json.load(read_file)
    
    
    @classmethod
    def set(cls, key: str, value):
        if not hasattr(cls, "_config"):
            cls._initConfig()
        cls._conf[key] = value
    
    @classmethod
    def get(cls, key: str):
        if not hasattr(cls, "_config"):
            cls._initConfig()
        return cls._conf[key]