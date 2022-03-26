from simulator.core.simulator import Simulator
from simulator.environment.task_environment import TaskEnvironment


class Driver:
    def run(taskEnvironment: TaskEnvironment):
        simulator = Simulator()
        taskEnvironment.setup(simulator)
        simulator.run()
        