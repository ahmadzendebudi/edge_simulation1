import numpy as np
a = np.arange(0.1, 1.1, 0.1)
b = np.arange(1, 5)
c = np.arange(1, 8)
lists = [a, b, c]
size = 1
for list in lists:
    size = size * len(list)
for i in range(0, size):
    remaining = i
    values = [] 
    for j in range(0, len(lists)):
        index = remaining % len(lists[j])
        remaining = int(remaining / len(lists[j]))
        values.append(lists[j][index])
    print(values)