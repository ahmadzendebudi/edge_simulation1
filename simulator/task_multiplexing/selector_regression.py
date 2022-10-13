
from collections import deque
import sys
from typing import Any, Callable, Deque, Sequence, Tuple
from simulator.core.task import Task
from simulator.dql.transition_agent import TransitionAgent
from simulator.processes.task_multiplexer import TaskMultiplexerSelector
from simulator import Config
from simulator import Common
from simulator import Logger

import tensorflow as tf
import numpy as np
from simulator.task_multiplexing.selector import MultiplexerSelectorBehaviour, MultiplexerSelectorModel

from simulator.task_multiplexing.transition import Transition

class TaskMultiplexerSelectorRegression(TaskMultiplexerSelector):
    
    def __init__(self, stateShape: Tuple[int], rewardFunction: Callable[[Transition], float], bufferSize: int = 10000,
                 trainInterval: int = 100, behaviour: MultiplexerSelectorBehaviour = None) -> None:
        super().__init__(rewardFunction, behaviour)
        
        self._trainInterval = trainInterval
        self._trainIntervalCounter = 0
        self._buffersize = bufferSize

        self.generateModel()

        self._buffer: Deque[Transition] = deque()


    def generateModel(self, normalizer = None):
        if (normalizer == None):
            normalizer = tf.keras.layers.Normalization(axis=-1)
        self._model = tf.keras.Sequential([
            normalizer,
            tf.keras.layers.Dense(units=1)
        ])
        #You might get an error saying that input size cannot be determined
        self._model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.1),
            loss='mean_absolute_error')
    
    def action(self, task: Task, state: Sequence[float]) -> Tuple[int, int]:
        state_action = np.stack([np.append(state, 0), np.append(state, 1)])
        predictions = self._model.predict(state_action)

        if np.random.random() > 0.05:
            if predictions[0][0] < predictions[1][0]:
                return [1, 1]
            else:
                return [0, 0]
        else:
            if np.random.random() < 0.5:
                return [1, 1]
            else:
                return [0, 0]
    
    def _addToBuffer(self, transition: Transition):
        self._buffer.append(transition)

        if (len(self._buffer) > self._buffersize) :
            self._buffer.popleft()

        self._trainIntervalCounter += 1
        if self._trainIntervalCounter > self._trainInterval:
            self._trainIntervalCounter = 0
            self._train()
            
    def _train(self) -> None:
        train_features = np.stack(map(lambda transaction: np.append(transaction.state1, transaction.action), self._buffer))
        train_labels = np.stack(map(lambda transaction: transaction.reward(), self._buffer))
        
        normalizer = tf.keras.layers.Normalization(axis=-1)
        normalizer.adapt(np.array(train_features))

        self.generateModel(normalizer)
        self._model.fit(
            train_features,
            train_labels,
            epochs=100,
            # Suppress logging.
            verbose=0,
            # Calculate validation results on 20% of the training data.
            validation_split = 0.2)
    

    def extractModel(self) -> MultiplexerSelectorModel:
        model = MultiplexerSelectorModel()
        model.model = self._model.variables()
        model.size = sys.getsizeof(self._model) #TODO check to see if it works correctly
        return model
    
    def setModel(self, model: MultiplexerSelectorModel):
        self._model.set_variables(model.model)
        pass
    