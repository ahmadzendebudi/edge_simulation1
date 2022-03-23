from tf_agents import trajectories
import random 
import numpy as np
import tensorflow as tf

class TransitionBuffer:
  def __init__(self, maxsize: int) -> None:
    self._maxsize = maxsize
    self._transition_buffer = [None] * maxsize
    self._head = 0
    self._size = 0
    pass
  
  def observer(self, transition: trajectories.Transition) -> None:
    self._put(transition)

  def elementAt(self, position: int) -> trajectories.Transition:
    return self._transition_buffer[(self._head - self._size + position) % self._maxsize]

  def _put(self, transition: trajectories.Transition) -> None:
    self._transition_buffer[self._head] = transition
    self._head = (self._head + 1) % self._maxsize
    if self._size < self._maxsize: self._size += 1

  def removeTail(self) -> trajectories.Transition:
    if self._size == 0:
      return None

    self._transition_buffer[(self._head - self._size) % self._maxsize] = None
    self._size -= 1
  
  #TODO for now, I only sample one batch of experience, in the future, I might need to have multiple batches
  def sampleExperiences(self, maxSampleSize: int, seed: int = None) -> trajectories.Transition:
    sampleSize = min(maxSampleSize, self._size)
    selection = random.sample(range(0, self._size), sampleSize)

    step_type = [None] * sampleSize
    observation = [None] * sampleSize
    action = [None] * sampleSize
    policy_info = [None] * sampleSize
    next_step_type = [None] * sampleSize
    reward = [None] * sampleSize
    discount = [None] * sampleSize

    index = 0
    for position in selection:
      trans = self._transition_buffer[position]
      traj1 = trajectories.from_transition(trans.time_step, trans.action_step, trans.next_time_step)
      traj2 = trajectories.from_transition(trans.next_time_step, trans.action_step, trans.next_time_step)
        
      step_type[index] = np.stack([traj1.step_type, traj2.step_type])
      observation[index] = np.stack([traj1.observation, traj2.observation])
      action[index] = np.stack([traj1.action, traj2.action])
      policy_info[index] = np.stack([traj1.policy_info, traj2.policy_info])
      next_step_type[index] = np.stack([traj1.next_step_type, traj2.next_step_type])
      reward[index] = np.stack([traj1.reward, traj2.reward])
      discount[index] = np.stack([traj1.discount, traj2.discount])
      
      index += 1

    return trajectories.Trajectory(
      step_type=tf.convert_to_tensor(np.stack(step_type)),
      observation=tf.convert_to_tensor(np.stack(observation)),
      action=tf.convert_to_tensor(np.stack(action)),
      policy_info=tf.convert_to_tensor(np.stack(policy_info)),
      next_step_type=tf.convert_to_tensor(np.stack(next_step_type)),
      reward=tf.convert_to_tensor(np.stack(reward)),
      discount=tf.convert_to_tensor(np.stack(discount)))