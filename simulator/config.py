import json

class Config:
    
    @classmethod
    def _initConfig(cls):
        with open("simulator/config.json", "r") as read_file:
            cls._conf = json.load(read_file)
    
    @classmethod
    def reset(cls):
        cls._config_updates = {}
    
    @classmethod
    def set(cls, key: str, value):
        if not hasattr(cls, "_config_updates"):
            cls._config_updates = {}
        cls._config_updates[key] = value
    
    @classmethod
    def get(cls, key: str):
        if hasattr(cls, "_config_updates"):
            result = cls._config_updates.get(key, None)
            if result != None:
                return result
        
        if not hasattr(cls, "_config"):
            cls._initConfig()
        return cls._conf[key]