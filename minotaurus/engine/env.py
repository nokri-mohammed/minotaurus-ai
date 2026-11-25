"""MazeEnv: one dot in one maze, Gymnasium interface."""

from __future__ import annotations

from typing import ClassVar

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from minotaurus.engine.levels import MOVES, Level
from minotaurus.engine.observe import DEFAULT_WINDOW, OBS_VERSION, obs_bounds, observe

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

    def __init__(self, level: Level, window: int = DEFAULT_WINDOW, obs_version: int = OBS_VERSION):
        self.level = level
        self.window = window
        self.obs_version = obs_version
        self.action_space = spaces.Discrete(4)
        low, high = obs_bounds(window, obs_version)
        self.observation_space = spaces.Box(low, high, dtype=np.float32)
        self.step_limit = level.step_limit
        self.pos = level.start
        # Visit count per square: the start counts once, and every step adds one to the square
        # the dot ends on, a bump too (the dot stays, so its own square counts again).
        self.visits: dict[tuple[int, int], int] = {level.start: 1}
        self.steps = 0
        # the memory that version 2 shows the brain: its last move and whether it bumped
        self.last_move: int | None = None
        self.bumped = False

    @property
    def visited(self) -> set[tuple[int, int]]:
        """The squares walked on at least once."""
        return set(self.visits)

    def _obs(self) -> np.ndarray:
        return observe(
            self.level,
            self.pos,
            self.visits,
            self.window,
            self.obs_version,
            self.last_move,
            self.bumped,
        )

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        self.pos = self.level.start
        self.visits = {self.pos: 1}
        self.steps = 0
        self.last_move = None
        self.bumped = False
        return self._obs(), {"pos": self.pos}

    def step(self, action: int):
        self.pos, bumped = move(self.level, self.pos, int(action))
        self.visits[self.pos] = self.visits.get(self.pos, 0) + 1
        self.steps += 1
        self.last_move = int(action)
        self.bumped = bumped
        terminated = self.pos == self.level.exit
        truncated = not terminated and self.steps >= self.step_limit
        if terminated:
            reward = REWARD_EXIT
        else:
            reward = REWARD_BUMP if bumped else REWARD_STEP
        return self._obs(), reward, terminated, truncated, {"pos": self.pos, "bumped": bumped}
