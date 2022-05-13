import numpy as np
import tensorflow as tf

from simulator.core.simulator import Simulator
from simulator import Config
from simulator.environment.task_environment import TaskEnvironment
from simulator.logger import LogOutputConsolePrint, Logger
from simulator.processes.task_generator import TaskGenerator
from simulator.world_builds.box_world import BoxWorld
from simulator.reporters import TransitionReporter
from simulator.task_multiplexing import TaskMultiplexerSelectorDql
from simulator.task_multiplexing import TaskMultiplexerSelectorLocal
from simulator.task_multiplexing import TaskMultiplexerSelectorRandom
from simulator.task_multiplexing import TaskMultiplexerSelectorRemote
from simulator.task_multiplexing import TaskMultiplexerSelectorGreedy


Logger.registerLogOutput(LogOutputConsolePrint())
np.random.seed(Config.get('random_seed'))
tf.random.set_seed(Config.get('random_seed'))


#generate task list: this is called here to make sure all selectors receive the same list of tuples
TaskGenerator.retrieveList()


world = BoxWorld()
edgeNodes, mobileNodes = world.build()
edgeReward, mobileReward = world.defaultRewards()



mobileReporter = TransitionReporter() 
edgeReporter = TransitionReporter() 


dqlSelectorGenerator = lambda state: TaskMultiplexerSelectorDql(state, Config.get("dql_training_buffer_size"))
localSelectorGenerator = lambda state: TaskMultiplexerSelectorLocal()
remoteSelectorGenerator = lambda state: TaskMultiplexerSelectorRemote()
randomSelectorGenerator = lambda state: TaskMultiplexerSelectorRandom()
greedySelectorGenerator = lambda state: TaskMultiplexerSelectorGreedy(state)

taskEnvironment = TaskEnvironment(edgeNodes, mobileNodes, 
                                  edgeSelectorGenerator= greedySelectorGenerator, 
                                  mobileSelectorGenerator= dqlSelectorGenerator,
                                  edgeRewardFunction= edgeReward,
                                  mobileRewardFunction=mobileReward)
simulator = Simulator()
taskEnvironment.initialize(simulator, [mobileReporter.addTransition], [edgeReporter.addTransition])
simulator.run()


print("mobile delay: " + str(mobileReporter.averageDelay()))
print("mobile power consumed: " + str(mobileReporter.averagePowerConsumed()))