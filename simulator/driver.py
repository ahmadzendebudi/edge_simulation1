from simulator.core.simulator import Simulator
from simulator.environment.task_environment import TaskEnvironment


class Driver:
    def run(self, taskEnvironment: TaskEnvironment):
        simulator = Simulator()
        taskEnvironment.initialize(simulator)
        simulator.run()
        