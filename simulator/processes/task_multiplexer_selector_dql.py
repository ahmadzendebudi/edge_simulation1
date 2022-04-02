from typing import Sequence
from simulator.core.task import Task
from simulator.processes.task_multiplexer import TaskMultiplexerSelector
from simulator import Config
from simulator import Logger
from simulator.util.transition_buffer import TransitionBuffer

import tensorflow as tf
from tf_agents import agents
from tf_agents import trajectories as tj
from tf_agents.typing import types
from tf_agents import networks
from tf_agents.networks import network
from tf_agents import utils
from tf_agents import specs
from tf_agents import policies
import numpy as np


class TaskMultiplexerSelectorDql(TaskMultiplexerSelector):
    
    def __init__(self, bufferSize: int = 10000) -> None:
        self._createAgent()
        self._collectPolicy = policies.py_tf_eager_policy.PyTFEagerPolicy(
            self._agent.collect_policy, use_tf_function=True)
        self._buffer = TransitionBuffer(bufferSize)
        super().__init__()
    
    def action(self, task: Task, state: Sequence[float]) -> tj.PolicyStep:
        #TODO for now, the agent always uses collect policy as the environment is essumed to evolve. 
        #otherwise, it should switch to policy after a while
        timeStep = None #TODO do the conversion
        return self._collectPolicy.action(timeStep)
    
    def select(self, task: Task, state: Sequence[float]) -> int:
        '''it should return None for local execution, otherwise the id of the destination node'''
        action = self.action(task, state).action
        if action == 0:
            return None
        else:
            return action #TODO it should return the the edge with lowest queue size
     
    def addToBuffer(self, transition: tj.Transition):
        self._buffer.put(transition)
            
    def train(self) -> None:
        experience = self._buffer.sampleExperiences(Config.get("dql_training_batch_size"))
        train_loss = self._agent.train(experience, None).loss
        if hasattr(self, '_trainCount'):
            self._trainCount += 1
        else:
            self._trainCount = 1
        
        if self._trainCount % 100 == 0:
            Logger.log("dql selector train loss after " + str(self._trainCount) + 
                       " times of training: " + str(train_loss), 2)
        elif self._trainCount % 25 == 0:
            Logger.log("dql selector train loss after " + str(self._trainCount) + 
                       " times of training: " + str(train_loss), 3)
           
    
    def _createAgent(self) -> None:
        optimizer = tf.keras.optimizers.Adam(learning_rate=Config.get("dql_learning_rate"))

        train_step_counter = tf.Variable(0)

        self._agent = agents.dqn.dqn_agent.DqnAgent(
            self._timestepTensorSpec(),
            self._actionTensorSpec(),
            self._qNetwork(),
            optimizer=optimizer,
            td_errors_loss_fn=utils.common.element_wise_squared_loss,
            train_step_counter=train_step_counter)

        self._agent.initialize()
    
    
    def _timestepTensorSpec(self) -> tj.TimeStep:
        return tj.time_step.time_step_spec(self._observation_spec(), self._reward_spec())
    
    def _observation_spec(self) -> types.NestedSpec:
        return specs.array_spec.BoundedArraySpec((5,), np.float32, 1, 3, 'observation')
        #TODO it should be passed on to the selector from the transition recorder or something
    
    def _reward_spec(self) -> types.NestedSpec:
        return specs.array_spec.ArraySpec(shape=(), dtype=np.float32, name='reward')
    
    def _actionTensorSpec(self) -> types.NestedTensorSpec:
        '''): local execution, 1: offload to the edge or the edge with lowest workload or something similar!!'''
        specs.array_spec.BoundedArraySpec((), np.int32, 0, 1, 'action')
    
    def _qNetwork(self) -> network.Network:
        fc_layer_params = (50, 20)
        action_tensor_spec = self._actionTensorSpec()
        num_actions = action_tensor_spec.maximum - action_tensor_spec.minimum + 1

        # Define a helper function to create Dense layers configured with the right
        # activation and kernel initializer.
        def dense_layer(num_units):
            return tf.keras.layers.Dense(
                num_units,
                activation=tf.keras.activations.relu,
                kernel_initializer=tf.keras.initializers.VarianceScaling(
                    scale=2.0, mode='fan_in', distribution='truncated_normal'))

        # QNetwork consists of a sequence of Dense layers followed by a dense layer
        # with `num_actions` units to generate one q_value per available action as
        # its output.
        dense_layers = [dense_layer(num_units) for num_units in fc_layer_params]
        q_values_layer = tf.keras.layers.Dense(
            num_actions,
            activation=None)
        q_net = networks.sequential.Sequential(dense_layers + [q_values_layer])
        return q_net
    