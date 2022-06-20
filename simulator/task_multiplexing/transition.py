
from typing import Callable

class Transition:
    def __init__(self, taskId: int, state1 = None, state2 = None, action = None, 
                 rewardFunction: Callable[['Transition'], float] = None,
                 delay: float = None, powerConsumed: float = None, completed = False,
                 taskWorkload = None) -> None:
        '''rewardFunction: (transition) -> reward'''
        self.taskId = taskId
        self.state1 = state1
        self.state2 = state2
        self.action = action
        self.delay = delay
        self.powerConsumed = powerConsumed
        self._rewardFunction = rewardFunction
        self.completed = completed
        self.taskWorkload = taskWorkload
    
    def reward(self):
        return self._rewardFunction(self)
    
    def __str__(self) -> str:
        return ("state1: " + str(self.state1) + " state2: " + str(self.state2) + " action: " +
                str(self.action) + " reward: " + str(self.reward()) + " delay: " + str(self.delay))
 