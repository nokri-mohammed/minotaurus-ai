"""Q-table method: a dict keyed on the whole observation."""

from __future__ import annotations

import random

import numpy as np

N_ACTIONS = 4
OBS_LEN = 77

# One fixed random weight per input. key = sum((obs + 1) * weight). 77 numbers do not fit in one
# 64-bit integer as plain bits, so the key is a hash, computed the same way in Python and inside
# the exported ONNX graph. Weights stay below 2**45 so the sum (at most 77 * 2 * 2**45) stays under
# 2**53: onnxruntime's integer ReduceSum is only exact up to 2**53 (it loses low bits above that).
KEY_WEIGHTS = np.random.default_rng(20261121).integers(1, 2**45, size=OBS_LEN, dtype=np.int64)


def obs_key(obs: np.ndarray) -> int:
    ints = (np.asarray(obs, dtype=np.float32).reshape(-1) + 1.0).astype(np.int64)
    return int(np.sum(ints * KEY_WEIGHTS, dtype=np.int64))


class QTableAgent:
    def __init__(
        self,
        learning_rate: float,
        gamma: float,
        epsilon_start: float,
        epsilon_end: float,
        epsilon_decay: float,
        seed: int = 0,
    ):
        self.lr = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.rng = random.Random(seed)
        self.q: dict[int, np.ndarray] = {}

    def row(self, key: int) -> np.ndarray:
        return self.q.get(key, np.zeros(N_ACTIONS, dtype=np.float32))

    def scores(self, obs: np.ndarray) -> np.ndarray:
        return self.row(obs_key(obs)).copy()

    def act(self, obs: np.ndarray, explore: bool = True) -> int:
        if explore and self.rng.random() < self.epsilon:
            return self.rng.randrange(N_ACTIONS)
        return int(np.argmax(self.scores(obs)))

    def update(self, obs, action: int, reward: float, next_obs, done: bool) -> float:
        key = obs_key(obs)
        row = self.q.setdefault(key, np.zeros(N_ACTIONS, dtype=np.float32))
        target = reward if done else reward + self.gamma * float(np.max(self.row(obs_key(next_obs))))
        error = target - float(row[action])
        row[action] += self.lr * error
        return abs(error)

    def end_episode(self) -> None:
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
