from array import array
from multiprocessing.dummy import Array

import numpy as np
from simulator import core 
import random
from tf_agents.trajectories import PolicyStep

from simulator.config import Config
from simulator.logger import Logger

Logger.log(Config.get("dql_learning_discount"), 1)