from simulator import core 
import random
randListId = []
randListTime = []
rng = range(0, 100006)
for i in rng:
    randListId.append(random.randint(1, 1 <<32))
    randListTime.append(random.random())

eheap = core.EventHeap()
for i in rng:
    eheap.addEvent(randListTime[i], randListId[i])
    
for i in range(0, 100000):
    eheap.nextEvent()
    
print(eheap.nextEvent())
print(eheap.nextEvent())
print(eheap.nextEvent())
print(eheap.nextEvent())