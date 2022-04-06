from array import array
from multiprocessing.dummy import Array

import numpy as np
from simulator import core 
import random
from tf_agents.trajectories import PolicyStep

a = PolicyStep(np.array(1), (), ())
print(a)