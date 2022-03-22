from __future__ import annotations

from tf_agents import specs
from tf_agents import typing
from tf_agents import trajectories

import numpy as np
import abc

class InterruptEnvironment:
  def __init__(self) -> None:
    self._current_interrupt = None

  def action_tensor_spec(self) -> typing.NestedArraySpec:
    return specs.tensor_spec.from_spec(self.action_spec())

  def reward_spec(self) -> typing.NestedArraySpec:
    return specs.array_spec.ArraySpec(shape=(), dtype=np.float32, name='reward')

  def time_step_tensor_spec(self) -> trajectories.time_step.TimeStep:
    return specs.tensor_spec.from_spec(self.time_step_spec())

  def time_step_spec(self) -> trajectories.time_step.TimeStep:
    return trajectories.time_step.time_step_spec(self.observation_spec(), self.reward_spec())

  def current_interrupt(self) -> InterruptEnvironment.Interrupt:
    return self._current_interrupt

  def reset(self) -> InterruptEnvironment.Interrupt:
    self._current_interrupt = self._reset()
    return self._current_interrupt

  def resume(self, actionStep: trajectories.policy_step.PolicyStep = None) -> InterruptEnvironment.Interrupt:
    self._current_interrupt = self._resume(actionStep)
    return self._current_interrupt

  @abc.abstractmethod
  def observation_spec(self) -> typing.NestedArraySpec:
    pass

  @abc.abstractmethod
  def action_spec(self) -> typing.NestedArraySpec:
    pass

  @abc.abstractmethod
  def _reset(self) -> InterruptEnvironment.Interrupt:
    pass

  @abc.abstractmethod
  def _resume(self, actionStep: trajectories.policy_step.PolicyStep = None) -> InterruptEnvironment.Interrupt:
    pass

  class Interrupt:
    def __init__(self, timeStep: trajectories.time_step.TimeStep, actionRequired = False,
     transitionCompleted = False, terminated = False,
     nextTimeStep: trajectories.time_step.TimeStep = None,
     actionStep: trajectories.policy_step.PolicyStep = None) -> None:
      self._timeStep = timeStep
      self._actionRequired = actionRequired
      self._transitionCompleted = transitionCompleted
      self._terminated = terminated
      self._nextTimeStep = nextTimeStep
      self._actionStep = actionStep

    def actionRequired(self):
      return self._actionRequired
    
    def transitionCompleted(self):
      return self._transitionCompleted
    
    def terminated(self):
      return self._terminated
    
    def timeStep(self):
      return self._timeStep
    
    def nextTimeStep(self):
      return self._nextTimeStep
    
    def actionStep(self):
      return self._actionStep