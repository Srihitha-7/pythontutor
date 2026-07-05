import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
from collections import deque


class DQN(nn.Module):
    def __init__(self, input_dim, output_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim)
        )

    def forward(self, x):
        return self.net(x)


class DQNAgent:
    def __init__(self, state_size, action_size,
                 lr=0.001, gamma=0.99,
                 memory_capacity=10_000,
                 target_update_freq=100):
        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma
        self.target_update_freq = target_update_freq
        self.learn_step = 0            # counts every learn() call

        self.model  = DQN(state_size, action_size)
        self.target = DQN(state_size, action_size)
        self._sync_target()            # initialise target == online

        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.loss_fn   = nn.MSELoss()

        # bounded replay buffer — prevents unbounded memory growth
        self.memory = deque(maxlen=memory_capacity)

    # ------------------------------------------------------------------ #
    #  Target-network sync                                                 #
    # ------------------------------------------------------------------ #
    def _sync_target(self):
        self.target.load_state_dict(self.model.state_dict())

    # ------------------------------------------------------------------ #
    #  Action selection (ε-greedy)                                         #
    # ------------------------------------------------------------------ #
    def act(self, state, epsilon):
        if random.random() < epsilon:
            return random.randint(0, self.action_size - 1)
        with torch.no_grad():
            state_t = torch.FloatTensor(state).unsqueeze(0)   # (1, state_size)
            q_values = self.model(state_t)
            return torch.argmax(q_values, dim=1).item()

    # ------------------------------------------------------------------ #
    #  Store transition                                                    #
    # ------------------------------------------------------------------ #
    def remember(self, s, a, r, s2, done):
        self.memory.append((s, a, r, s2, done))

    # ------------------------------------------------------------------ #
    #  Learn from a random mini-batch                                      #
    # ------------------------------------------------------------------ #
    def learn(self, batch_size=64):
        """
        Sample a mini-batch, compute Bellman targets with the frozen
        target network, back-propagate through the online network, and
        periodically hard-copy weights to the target network.

        Returns the scalar loss for logging, or None if the buffer is
        too small.
        """
        if len(self.memory) < batch_size:
            return None

        batch = random.sample(self.memory, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states_t      = torch.FloatTensor(states)
        actions_t     = torch.LongTensor(actions).unsqueeze(1)
        rewards_t     = torch.FloatTensor(rewards).unsqueeze(1)
        next_states_t = torch.FloatTensor(next_states)
        dones_t       = torch.FloatTensor(dones).unsqueeze(1)

        # Current Q-values for the actions actually taken
        q_current = self.model(states_t).gather(1, actions_t)

        # Bellman target — no gradient through the target network
        with torch.no_grad():
            q_next   = self.target(next_states_t).max(dim=1, keepdim=True).values
            q_target = rewards_t + self.gamma * q_next * (1.0 - dones_t)

        loss = self.loss_fn(q_current, q_target)

        self.optimizer.zero_grad()
        loss.backward()
        # gradient clipping for stability
        nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        self.optimizer.step()

        self.learn_step += 1
        if self.learn_step % self.target_update_freq == 0:
            self._sync_target()

        return loss.item()