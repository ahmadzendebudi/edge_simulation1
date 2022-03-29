
import numpy as np
from simulator.core.simulator import Simulator
from simulator import Config
from simulator.environment.task_environment import TaskEnvironment
from simulator.logger import LogOutputConsolePrint, Logger
from simulator.world_builds.box_world import BoxWorld

if True:
    Logger.registerLogOutput(LogOutputConsolePrint())
    np.random.seed(Config.get('random_seed'))
    
    world = BoxWorld()
    edgeNodes, mobileNodes = world.build()

    taskEnvironment = TaskEnvironment(edgeNodes, mobileNodes)
    simulator = Simulator()
    taskEnvironment.initialize(simulator)
    simulator.run()