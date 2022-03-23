import random

class Seeder:
    def __init__(self, initialSeed = None) -> None:
        if (initialSeed == None):
            initialSeed = random.randint(1, 1 << 32)
        self._initialValue = initialSeed
        pass
    def next(self) -> int:
        self._initialValue += 1
        return self._initialValue