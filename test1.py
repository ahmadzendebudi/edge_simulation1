import queue
from simulator.core import Task

t = Task(235, 23, 53, 54325)
print(t)
q = queue.Queue()

q.put(123)
q.put(3435)

print(q.get())
print(q.get())