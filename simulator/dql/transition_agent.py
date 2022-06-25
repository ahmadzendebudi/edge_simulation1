from abc import abstractmethod
from simulator import Config
from simulator import Logger
from simulator.dql.transition_buffer import TransitionBuffer

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

class TransitionAgent:
    
    def __init__(self, observation_spec: types.NestedSpec, action_spec: types.NestedSpec, bufferSize: int) -> None:
        self._observation_spec = observation_spec
        self._action_spec = action_spec
        self._buffer = TransitionBuffer(bufferSize)
        self._createAgent()
        self._collectPolicy = policies.py_tf_eager_policy.PyTFEagerPolicy(
            self._agent.collect_policy, use_tf_function=True)
        self._policy = policies.py_tf_eager_policy.PyTFEagerPolicy(
            self._agent.policy, use_tf_function=True)
        super().__init__()
        
    
    def action(self, timeStep: tj.TimeStep, collectPolicy = False) -> tj.PolicyStep:
        if collectPolicy:
            return self._collectPolicy.action(timeStep)
        else:
            return self._policy.action(timeStep)
    
    def qvalue(self, timeStep: tj.TimeStep):
        #TODO to be implemented
        pass
    
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
        return specs.tensor_spec.from_spec(
            tj.time_step.time_step_spec(self._observation_spec, self._reward_spec()))
    
    def _reward_spec(self) -> types.NestedSpec:
        return specs.array_spec.ArraySpec(shape=(), dtype=np.float32, name='reward')
    
    def _actionTensorSpec(self) -> types.NestedTensorSpec:
        return specs.tensor_spec.from_spec(self._action_spec)
    
    def _qNetwork(self) -> network.Network:
        #fc_layer_params = (100, 100, 50, 20)
        fc_layer_params = (128, 128)
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
        #dropout_layer = tf.keras.layers.Dropout(0.8)
        q_values_layer = tf.keras.layers.Dense(
            num_actions,
            activation=None)
        q_net = networks.sequential.Sequential(dense_layers + [q_values_layer])
        return q_net

    def variables(self):
        return self._agent._q_network.variables

    def set_variables(self, variables):
        for a, b in zip(self._agent._q_network.variables, variables):
            a.assign(b)

    
    