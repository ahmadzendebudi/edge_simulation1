from typing import Any, Callable, Sequence, Optional
from InterruptEnvironment import InterruptEnvironment as InterruptEnv
from tf_agents import trajectories
from tf_agents import policies
from tf_agents.typing import types

class InterruptDriver:
  def __init__(
      self,
      env: InterruptEnv,
      policy: policies.py_policy.PyPolicy,
      transition_observers: Sequence[Callable[[trajectories.Transition],
                                                       Any]] = []):
    self._env = env
    self._policy = policy
    self._transition_observers = transition_observers

  def run(self, max_transitions: int, policy_state: types.NestedArray = ()) -> types.NestedArray:
    if (self._env.current_interrupt() == None):
      self._env.reset()

    transition_counter = 0
    interrupt = self._env.current_interrupt()
    while transition_counter < max_transitions and not interrupt.terminated():
      if interrupt.actionRequired():
        action_step = self._policy.action(interrupt.timeStep(), policy_state)
        action_step_with_previous_state = action_step._replace(state=policy_state)
        policy_state = action_step.state
        interrupt = self._env.resume(action_step_with_previous_state)
      elif interrupt.transitionCompleted():
        if(interrupt.timeStep().step_type == trajectories.time_step.StepType.LAST):
          raise ValueError("Environment is in 'last' step type. Cannot store transition")
        for observer in self._transition_observers:
          observer(trajectories.Transition(time_step = interrupt.timeStep(), 
                                          action_step = interrupt.actionStep(),
                                          next_time_step = interrupt.nextTimeStep()))
        transition_counter += 1
        interrupt = self._env.resume()

    return policy_state