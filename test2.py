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

varients = []
varients.append({"step": 1, "config": "task_generator_lambda", "values": np.arange(0.1, 1.1, 0.1)})
varients.append({"step": 2, "config": "boxworld_mobile_nodes", "values": [50, 75, 100, 150, 200]})

reportMap = []

step = 0
hasStep = True
while hasStep:
    step += 1
    hasStep = False
    currentVariants = []
    for varient in varients:
        if varient["step"] == step:
            currentVariants.append(varient)
            hasStep = True        
    size = 1
    for varient in currentVariants:
        size = size * len(varient["values"])
    for i in range(0, size):
        remaining = i
        values = [] 
        for j in range(0, len(currentVariants)):
            valuesCount = len(currentVariants[j]["values"])
            index = remaining % valuesCount
            remaining = int(remaining / valuesCount)
            values.append({"config": currentVariants[j]["config"], "values": currentVariants[j]["values"][index]})
        print("i(" + str(i) + ")" + str(values))
    