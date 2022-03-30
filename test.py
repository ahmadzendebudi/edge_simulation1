from simulator import core 
import random

a = {}
a[2] = [2, "sdfdfg"]
a[4] = [4, "dsgdfbdg"]
a[3] = [3, "435435"]
a[6] = [6, ":)"]
a[7] = [7, "4354346"]
a[13] = [13, "4354346"]
a[21] = [21, "4354346"]
a[15] = [15, "4354346"]
a[18] = [18, ":)"]
a[20] = [20, ":)"]
a[30] = [30, ":)"]
a[10] = [10, ":)"]

for b in a.values():
    if b[0] % 2 == 1:
        a.pop(b[0])
print(a)