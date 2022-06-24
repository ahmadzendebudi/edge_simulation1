from simulation_assist import SimulationAssist


runIdentifier = "A"

varients = []
#varients.append({"step": 1, "config": "task_generator_lambda", "values": np.arange(0.1, 1.1, 0.1)})
step = 0

step += 1
varients.append({"step": step, "config": "edge_selector", "values": ["dql"]})
varients.append({"step": step, "config": "mobile_selector", "values": ["dql"]})
varients.append({"step": step, "config": "boxworld_mobile_nodes", "values": [75]})
varients.append({"step": step, "config": "task_generator_lambda", "values": [0.75]})

step += 1
varients.append({"step": step, "config": "edge_selector", "values": ["greedy"]})
varients.append({"step": step, "config": "mobile_selector", "values": ["greedy"]})
varients.append({"step": step, "config": "boxworld_mobile_nodes", "values": [75]})
varients.append({"step": step, "config": "task_generator_lambda", "values": [0.75]})


"""
step += 1
varients.append({"step": step, "config": "edge_selector", "values": ["dql"]})
varients.append({"step": step, "config": "mobile_selector", "values": ["dql"]})
varients.append({"step": step, "config": "boxworld_mobile_nodes", "values": [50, 75]})
varients.append({"step": step, "config": "task_generator_lambda", "values": [0.25, 0.5, 0.75, 1]})

step += 1
varients.append({"step": step, "config": "edge_selector", "values": ["dql"]})
varients.append({"step": step, "config": "mobile_selector", "values": ["dql"]})
varients.append({"step": step, "config": "boxworld_mobile_nodes", "values": [25, 100, 150]})
varients.append({"step": step, "config": "task_generator_lambda", "values": [0.5, 0.75]})


step += 1
varients.append({"step": step, "config": "edge_selector", "values": ["greedy"]})
varients.append({"step": step, "config": "mobile_selector", "values": ["greedy"]})
varients.append({"step": step, "config": "boxworld_mobile_nodes", "values": [50, 75]})
varients.append({"step": step, "config": "task_generator_lambda", "values": [0.25, 0.5, 0.75, 1]})

step += 1
varients.append({"step": step, "config": "edge_selector", "values": ["greedy"]})
varients.append({"step": step, "config": "mobile_selector", "values": ["greedy"]})
varients.append({"step": step, "config": "boxworld_mobile_nodes", "values": [25, 100, 150]})
varients.append({"step": step, "config": "task_generator_lambda", "values": [0.5, 0.75]})

step += 1
varients.append({"step": step, "config": "edge_selector", "values": ["local"]})
varients.append({"step": step, "config": "mobile_selector", "values": ["random", "local", "remote"]})
varients.append({"step": step, "config": "boxworld_mobile_nodes", "values": [50, 75]})
varients.append({"step": step, "config": "task_generator_lambda", "values": [0.25, 0.5, 0.75, 1]})

step += 1
varients.append({"step": step, "config": "edge_selector", "values": ["local"]})
varients.append({"step": step, "config": "mobile_selector", "values": ["random", "local", "remote"]})
varients.append({"step": step, "config": "boxworld_mobile_nodes", "values": [25, 100, 150]})
varients.append({"step": step, "config": "task_generator_lambda", "values": [0.5, 0.75]})
"""
SimulationAssist.runBatchSimulation(varients, runIdentifier)