"""Q-table method: a dict keyed on the whole observation."""

from __future__ import annotations

import random

import numpy as np

from minotaurus.engine.observe import blocked_moves, free_moves

N_ACTIONS = 4
OBS_LEN = 77

# One fixed random weight per input. key = sum((obs + 1) * weight). 77 numbers do not fit in one
# 64-bit integer as plain bits, so the key is a hash, computed the same way in Python and inside
# the exported ONNX graph. Weights stay below 2**45 so the sum (at most 77 * 2 * 2**45) stays under
# 2**53: onnxruntime's integer ReduceSum is only exact up to 2**53 (it loses low bits above that).
KEY_WEIGHTS = np.random.default_rng(20261121).integers(1, 2**45, size=OBS_LEN, dtype=np.int64)


def obs_key(obs: np.ndarray) -> int:
    """The table key of an observation. The visited layer counts as yes/no here: any visit count
    above 1 is read as 1 (min(x, 1) on every input, which changes only the counts), so the key is
    the same as before visit counts and a table keeps its size."""
    capped = np.minimum(np.asarray(obs, dtype=np.float32).reshape(-1), 1.0)
    ints = (capped + 1.0).astype(np.int64)
    return int(np.sum(ints * KEY_WEIGHTS, dtype=np.int64))


def best_move(scores: np.ndarray, obs: np.ndarray, wall_mask: bool) -> int:
    """The move with the highest score; with the wall mask, never a move into a visible wall.
    A tie goes to the first move in order (up, down, left, right), as np.argmax does."""
    if not wall_mask:
        return int(np.argmax(scores))
    blocked = blocked_moves(obs)
    best = None
    for action in range(N_ACTIONS):
        if blocked[action]:
            continue
        if best is None or scores[action] > scores[best]:
            best = action
    return best


class QTableAgent:
    def __init__(
        self,
        learning_rate: float,
        gamma: float,
        epsilon_start: float,
        epsilon_end: float,
        epsilon_decay: float,
        seed: int = 0,
        wall_mask: bool = False,
    ):
        self.lr = learning_rate
        # never pick a move into a visible wall (random and best moves, and the learning target)
        self.wall_mask = wall_mask
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

    def best_value(self, obs: np.ndarray) -> float:
        """The highest score of `obs`, among the free moves when the wall mask is on."""
        row = self.row(obs_key(obs))
        if not self.wall_mask:
            return float(np.max(row))
        best = None
        for action in free_moves(obs):
            if best is None or row[action] > best:
                best = float(row[action])
        return best

    def act(self, obs: np.ndarray, explore: bool = True) -> int:
        if explore and self.rng.random() < self.epsilon:
            if self.wall_mask:
                return self.rng.choice(free_moves(obs))
            return self.rng.randrange(N_ACTIONS)
        return best_move(self.scores(obs), obs, self.wall_mask)

    def update(self, obs, action: int, reward: float, next_obs, done: bool) -> float:
        key = obs_key(obs)
        row = self.q.setdefault(key, np.zeros(N_ACTIONS, dtype=np.float32))
        target = reward if done else reward + self.gamma * self.best_value(next_obs)
        error = target - float(row[action])
        row[action] += self.lr * error
        return abs(error)

    def end_episode(self) -> None:
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
