
from simulator.common import Common
from simulator.core.simulator import Simulator
from simulator.core.task import Task
from simulator.core.task_queue import TaskQueue


queue = TaskQueue(Common.generateUniqueId())
simulator = Simulator()
simulator.registerTaskQueue(queue)

t = Task(12,43, 1)
simulator.registerTask(t)

queue.put(t)
print(queue.get())
print(queue.qsize() == 0)