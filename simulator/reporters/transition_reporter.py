

from abc import abstractmethod
from simulator.task_multiplexing import Transition

class TransitionReporter:
    def __init__(self) -> None:
        self.transitionList = []
    
    def addTransition(self, transition: Transition):
        self.transitionList.append(transition)
    
    def averageDelay(self):
        return sum(map(lambda t: t.delay, self.transitionList))/len(self.transitionList)
    
    def averagePowerConsumed(self):
        return sum(map(lambda t: t.powerConsumed, self.transitionList))/len(self.transitionList)