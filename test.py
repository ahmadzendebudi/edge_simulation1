from simulator import core 
import random

class b:
    def wake(self):
        pass

class a:
    def m(self):
        self._a = 45

    def get(self):
        return self._a
    
aaa = a()
bbb = b()
bbb.wake = aaa.m
bbb.wake()
print(aaa._a)
print(bbb._a)

    
