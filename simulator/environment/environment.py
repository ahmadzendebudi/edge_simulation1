from simulator import environment as env
  
class Environment:
    def __init__(self, edgeNodes: dict[int, env.EdgeNode], mobileNodes: dict[int, env.MobileNode]) -> None:
        self._edgeNodes = edgeNodes
        self._mobileNodes = mobileNodes
    