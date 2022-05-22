

from abc import abstractmethod
import pickle
import time
from typing import Collection
from simulator.common import Common
from simulator.task_multiplexing import Transition
from simulator.core import Task
from simulator.core import Simulator
from pathlib import Path

class TransitionReporterItem:
    def __init__(self, task: Task, delay: float, powerConsumption: float, reward: float, action: int) -> None:
        self.task = task
        self.delay = delay
        self.powerConsumtion = powerConsumption
        self.reward = reward
        self.action = action
         
class TransitionReporter:
    def __init__(self, simulator: Simulator, path) -> None:
        self._simulator = simulator
        self.path = path
        self.transitionList = []
    
    def addTransition(self, transition: Transition):
        item = TransitionReporterItem(self._simulator.getTask(transition.taskId),
                                      transition.delay,
                                      transition.powerConsumed,
                                      transition.reward(),
                                      transition.action)
        self.transitionList.append(item)
    
    def averageDelay(self):
        return sum(map(lambda t: t.delay, self.transitionList))/len(self.transitionList)
    
    def averagePowerConsumed(self):
        return sum(map(lambda t: t.powerConsumtion, self.transitionList))/len(self.transitionList)
    
    def pickle(self):
        with open(self.path, 'wb') as f:
            pickle.dump(self.transitionList, f)
            
    @classmethod       
    def getListFromPickle(cls, fromPickle: str) -> Collection[TransitionReporterItem]:
        with open(fromPickle, 'rb') as f:
            return pickle.load(f)