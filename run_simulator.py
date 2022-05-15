import time
import numpy as np
import tensorflow as tf

from simulator.core.simulator import Simulator
from simulator import Config
from simulator.environment.task_environment import TaskEnvironment
from simulator.logger import LogOutputConsolePrint, LogOutputTextFile, Logger
from simulator.processes.task_generator import TaskGenerator
from simulator.world_builds.box_world import BoxWorld
from simulator.reporters import TransitionReporter
from simulator.task_multiplexing import TaskMultiplexerSelectorDql
from simulator.task_multiplexing import TaskMultiplexerSelectorLocal
from simulator.task_multiplexing import TaskMultiplexerSelectorRandom
from simulator.task_multiplexing import TaskMultiplexerSelectorRemote
from simulator.task_multiplexing import TaskMultiplexerSelectorGreedy
from simulator import Common


#Common.setSimulationRunId("dql3")

Logger.registerLogOutput(LogOutputConsolePrint())
Logger.registerLogOutput(LogOutputTextFile("log\log" + Common.simulationRunId() + ".log"))
np.random.seed(Config.get('random_seed'))
tf.random.set_seed(Config.get('random_seed'))


#generate task list: this is called here to make sure all selectors receive the same list of tuples
TaskGenerator.retrieveList()


world = BoxWorld()
edgeNodes, mobileNodes = world.build()
edgeReward, mobileReward = world.defaultRewards()

simulator = Simulator()

mobileReporter = TransitionReporter(simulator, "mobile") 
edgeReporter = TransitionReporter(simulator, "edge") 

dqlSelectorGenerator = lambda state: TaskMultiplexerSelectorDql(state, Config.get("dql_training_buffer_size"))
localSelectorGenerator = lambda state: TaskMultiplexerSelectorLocal()
remoteSelectorGenerator = lambda state: TaskMultiplexerSelectorRemote()
randomSelectorGenerator = lambda state: TaskMultiplexerSelectorRandom()
greedySelectorGenerator = lambda state: TaskMultiplexerSelectorGreedy(state)

taskEnvironment = TaskEnvironment(edgeNodes, mobileNodes, 
                                  edgeSelectorGenerator= dqlSelectorGenerator, 
                                  mobileSelectorGenerator= dqlSelectorGenerator,
                                  edgeRewardFunction= edgeReward,
                                  mobileRewardFunction=mobileReward)
taskEnvironment.initialize(simulator, [mobileReporter.addTransition], [edgeReporter.addTransition])
simulator.run()


Logger.log("mobile delay: " + str(mobileReporter.averageDelay()), 0)
Logger.log("mobile power consumed: " + str(mobileReporter.averagePowerConsumed()), 0)

Logger.closeLogOutputs()
mobileReporter.pickle()
edgeReporter.pickle()