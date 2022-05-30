import json
import numpy as np
import tensorflow as tf
from pathlib import Path
    
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

class SimulationAssist:
    @classmethod
    def runBatchSimulation(cls, varients, runIdentifier):
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
            if (hasStep):
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
                        values.append({"config": currentVariants[j]["config"], "value": currentVariants[j]["values"][index]})
                    print("i(" + str(i) + ")" + str(values))
                
                    Config.reset()
                    for value in values:
                        Config.set(value["config"], value["value"])
                    
                    #Set up simulation id
                    Common.simulationResetRunId()
                    #Run simulation
                    cls.runSimulation(runIdentifier)
                    #Save a reference to simulation results for this run
                    reportMap.append({"runId": Common.simulationRunId(), "varient": values}) 
        
                    Path("results/reportMaps").mkdir(parents=True, exist_ok=True)
                    with open("results/reportMaps/reportMap{id}.json".format(id = runIdentifier), "a") as f:
                        f.truncate(0)
                        json.dump(reportMap, f)    
            
    @classmethod
    def runSimulation(cls, batchRunIdentifier = None):
        Logger.unregisterAllOutPut()
        Logger.registerLogOutput(LogOutputConsolePrint())
        logPath = "results/log/"
        reportPath = "results/report/"
        if (batchRunIdentifier != None):
            logPath += batchRunIdentifier + "/"
            reportPath += batchRunIdentifier + "/"
        Path(logPath).mkdir(parents=True, exist_ok=True)
        Path(reportPath).mkdir(parents=True, exist_ok=True)
            
        Logger.registerLogOutput(LogOutputTextFile(logPath + "log" + Common.simulationRunId() + ".log"))
        np.random.seed(Config.get('random_seed'))
        tf.random.set_seed(Config.get('random_seed'))


        #generate task list: this is called here to make sure all selectors receive the same list of tuples
        TaskGenerator.retrieveList()


        world = BoxWorld()
        edgeNodes, mobileNodes = world.build()
        edgeReward, mobileReward = world.defaultRewards()

        simulator = Simulator()
        mobileReportPath = reportPath + 'reportmobile' + Common.simulationRunId() + ".pkl"
        edgeReportPath = reportPath + 'reportedge' + Common.simulationRunId() + ".pkl"
        mobileReporter = TransitionReporter(simulator, mobileReportPath) 
        edgeReporter = TransitionReporter(simulator, edgeReportPath) 

        selectors = {
            "dql": lambda state: TaskMultiplexerSelectorDql(state, Config.get("dql_training_buffer_size"), 
                                                            Config.get("dql_training_interval")),
            "local": lambda state: TaskMultiplexerSelectorLocal(),
            "remote": lambda state: TaskMultiplexerSelectorRemote(),
            "random": lambda state: TaskMultiplexerSelectorRandom(),
            "greedy": lambda state: TaskMultiplexerSelectorGreedy(state)
        }

        
        taskEnvironment = TaskEnvironment(edgeNodes, mobileNodes, 
                                        edgeSelectorGenerator= selectors[Config.get("edge_selector")], 
                                        mobileSelectorGenerator= selectors[Config.get("mobile_selector")],
                                        edgeRewardFunction= edgeReward,
                                        mobileRewardFunction=mobileReward)
        taskEnvironment.initialize(simulator, [mobileReporter.addTransition], [edgeReporter.addTransition])
        simulator.run()

        Logger.log("mobile delay: " + str(mobileReporter.averageDelay()), 0)
        Logger.log("mobile power consumed: " + str(mobileReporter.averagePowerConsumed()), 0)

        Logger.closeLogOutputs()
        mobileReporter.pickle()
        edgeReporter.pickle()
            