
import numpy as np
from simulator.driver import Driver
from simulator.environment.task_environment import TaskEnvironment
from simulator.logger import LogOutputConsolePrint, Logger
from simulator.world_builds.box_world import BoxWorld

Logger.registerLogOutput(LogOutputConsolePrint())

world = BoxWorld()
edgeNodes, mobileNodes = world.build()

taskEnvironment = TaskEnvironment(edgeNodes, mobileNodes)
driver = Driver()
driver.run(taskEnvironment)