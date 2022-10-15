

from abc import abstractmethod
import pickle
import time
from typing import Collection
from simulator.common import Common
from simulator.task_multiplexing import Transition
from simulator.core import Task
from simulator.core import Simulator
from pathlib import Path

class UtilizationReporterItem:
    def __init__(self, task: Task, runTime: float, runStart: float) -> None:
        self.task = task
        self.runTime = runTime
        self.runStart = runStart
         
class UtilizationReporter:
    def __init__(self, path) -> None:
        self.path = path
        self.utilizationList = []
    
    def addUtilization(self, task: Task, runTime: float, runStart: float):
        item = UtilizationReporterItem(task, runTime, runStart)
        self.utilizationList.append(item)
    
    def averageUtilization(self):
        return sum(map(lambda t: t.runTime, self.utilizationList))/len(self.utilizationList)
    
    def pickle(self):
        with open(self.path, 'wb') as f:
            pickle.dump(self.utilizationList, f)
            
    @classmethod       
    def getListFromPickle(cls, fromPickle: str) -> Collection[UtilizationReporterItem]:
        with open(fromPickle, 'rb') as f:
            return pickle.load(f)