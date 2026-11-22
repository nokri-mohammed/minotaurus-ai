"""DQN method: MLP 77 -> hidden -> 4, replay buffer, target network, Adam, Huber loss."""

from __future__ import annotations

import random

import numpy as np
import torch
from torch import nn

from minotaurus.trainer.qtable import N_ACTIONS, OBS_LEN


def build_mlp(hidden_layers: list[int]) -> nn.Sequential:
    layers: list[nn.Module] = []
    size = OBS_LEN
    for width in hidden_layers:
        layers += [nn.Linear(size, width), nn.ReLU()]
        size = width
    layers.append(nn.Linear(size, N_ACTIONS))
    return nn.Sequential(*layers)


class DQNAgent:
    def __init__(
        self,
        hidden_layers: list[int],
        learning_rate: float,
        batch_size: int,
        gamma: float,
        replay_size: int,
        target_update: int,
        epsilon_start: float,
        epsilon_end: float,
        epsilon_decay: float,
        seed: int = 0,
    ):
        torch.manual_seed(seed)
        torch.set_num_threads(1)
        self.net = build_mlp(hidden_layers)
        self.target = build_mlp(hidden_layers)
        self.target.load_state_dict(self.net.state_dict())
        self.opt = torch.optim.Adam(self.net.parameters(), lr=learning_rate)
        self.batch_size = batch_size
        self.gamma = gamma
        self.replay_size = replay_size
        self.target_update = target_update
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.rng = random.Random(seed)
        self.buffer: list[tuple] = []
        self.pos = 0
        self.steps = 0

    def scores(self, obs: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            x = torch.as_tensor(np.asarray(obs, dtype=np.float32)).reshape(1, -1)
            return self.net(x)[0].numpy()

    def act(self, obs: np.ndarray, explore: bool = True) -> int:
        if explore and self.rng.random() < self.epsilon:
            return self.rng.randrange(N_ACTIONS)
        return int(np.argmax(self.scores(obs)))

    def remember(self, obs, action: int, reward: float, next_obs, done: bool) -> None:
        item = (np.array(obs, dtype=np.float32), action, reward,
                np.array(next_obs, dtype=np.float32), float(done))
        if len(self.buffer) < self.replay_size:
            self.buffer.append(item)
        else:
            self.buffer[self.pos] = item
        self.pos = (self.pos + 1) % self.replay_size

    def learn(self, batch: list[tuple] | None = None) -> float | None:
        """One gradient step on a batch (random from the buffer unless given). Returns the loss."""
        if batch is None:
            if len(self.buffer) < self.batch_size:
                return None
            batch = self.rng.sample(self.buffer, self.batch_size)
        obs, act, rew, nxt, done = (np.array(col) for col in zip(*batch, strict=True))
        obs_t = torch.as_tensor(obs, dtype=torch.float32)
        nxt_t = torch.as_tensor(nxt, dtype=torch.float32)
        act_t = torch.as_tensor(act, dtype=torch.int64).unsqueeze(1)
        rew_t = torch.as_tensor(rew, dtype=torch.float32)
        done_t = torch.as_tensor(done, dtype=torch.float32)
        with torch.no_grad():
            best = self.target(nxt_t).max(dim=1).values
            target = rew_t + self.gamma * best * (1.0 - done_t)
        pred = self.net(obs_t).gather(1, act_t).squeeze(1)
        loss = nn.functional.smooth_l1_loss(pred, target)
        self.opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.net.parameters(), 10.0)
        self.opt.step()
        return float(loss.item())

    def step(self, obs, action: int, reward: float, next_obs, done: bool) -> float | None:
        self.remember(obs, action, reward, next_obs, done)
        self.steps += 1
        loss = self.learn()
        if self.steps % self.target_update == 0:
            self.target.load_state_dict(self.net.state_dict())
        return loss

    def end_episode(self) -> None:
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
