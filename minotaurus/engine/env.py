"""MazeEnv: one dot in one maze, Gymnasium interface."""

from __future__ import annotations

from typing import ClassVar

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from minotaurus.engine.levels import MOVES, Level
from minotaurus.engine.observe import DEFAULT_WINDOW, obs_size, observe

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

REWARD_EXIT = 1.0
REWARD_STEP = -0.01
REWARD_BUMP = -0.05


def move(level: Level, pos: tuple[int, int], action: int) -> tuple[tuple[int, int], bool]:
    """Apply one action. Returns (new position, bumped). A move into a wall changes nothing."""
    dx, dy = MOVES[action]
    nxt = (pos[0] + dx, pos[1] + dy)
    if level.is_wall(*nxt):
        return pos, True
    return nxt, False


class MazeEnv(gym.Env):
    metadata: ClassVar[dict] = {"render_modes": []}

    def __init__(self, level: Level, window: int = DEFAULT_WINDOW):
        self.level = level
        self.window = window
        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(-1.0, 1.0, shape=(obs_size(window),), dtype=np.float32)
        self.step_limit = level.step_limit
        self.pos = level.start
        self.visited: set[tuple[int, int]] = {level.start}
        self.steps = 0

    def _obs(self) -> np.ndarray:
        return observe(self.level, self.pos, self.visited, self.window)

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self.pos = self.level.start
        self.visited = {self.pos}
        self.steps = 0
        return self._obs(), {"pos": self.pos}

    def step(self, action: int):
        self.pos, bumped = move(self.level, self.pos, int(action))
        self.visited.add(self.pos)
        self.steps += 1
        terminated = self.pos == self.level.exit
        truncated = not terminated and self.steps >= self.step_limit
        if terminated:
            reward = REWARD_EXIT
        else:
            reward = REWARD_BUMP if bumped else REWARD_STEP
        return self._obs(), reward, terminated, truncated, {"pos": self.pos, "bumped": bumped}
