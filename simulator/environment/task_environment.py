
from simulator.core.process import ProcessPlug
from simulator.core.simulator import Simulator
from simulator.core.task_queue import TaskQueuePlug
from simulator.environment.edge_node import EdgeNode
from simulator.environment.mobile_node import MobileNode
from simulator.core.environment import Environment

class TaskEnvironmentPlug:
    pass
class TaskEnvironment(Environment):
    def __init__(self, edgeNodes: dict[int, EdgeNode], mobileNodes: dict[int, MobileNode]) -> None:
        self._edgeNodes = edgeNodes
        self._mobileNodes = mobileNodes
    
    def setup(self, processPlug: ProcessPlug, taskQueuePlug: TaskQueuePlug) -> None:
        for edgeNode in self._edgeNodes:
            edgeNode.setup(processPlug, taskQueuePlug)
        for mobileNode in self._mobileNodes:
            mobileNode.setup(processPlug, taskQueuePlug)
    
    def edgeNode(self, id: int) -> EdgeNode:
        return self._edgeNodes[id]
    
    def mobileNode(self, id: int) -> MobileNode:
        return self._mobileNodes[id]