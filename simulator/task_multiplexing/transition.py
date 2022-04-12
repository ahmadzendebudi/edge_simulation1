
from typing import Sequence
import numpy as np
from tf_agents import trajectories as tj
from tf_agents import specs
from simulator.config import Config

class Transition:
    delay_coefficient = Config.get("delay_coefficient")
    power_coefficient = Config.get("power_coefficient")
    
    def __init__(self, taskId, state1 = None, state2 = None, action = None, delay = None, powerConsumed = None, completed = False) -> None:
        self.taskId = taskId
        self.state1 = state1
        self.state2 = state2
        self.action = action
        self.delay = delay
        self.powerConsumed = powerConsumed
        self.completed = completed
    
    def reward(self):
        #TODO compute reward properly
        #TODO introduce a deadline penalty: it should be implemented either here or in DRL code
        return - Transition.delay_coefficient * self.delay - Transition.power_coefficient * self.powerConsumed
 