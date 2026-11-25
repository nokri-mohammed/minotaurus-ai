"""Race: two dots on one level, moves applied at once. Brains are plain functions."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

from minotaurus.engine.env import move
from minotaurus.engine.levels import Level
from minotaurus.engine.observe import DEFAULT_WINDOW, OBS_VERSION, observe

TICK_SECONDS = 0.1

Brain = Callable[[np.ndarray], int]


@dataclass(frozen=True)
class RaceResult:
    winner: int | None  # 0 or 1; None on a draw or when nobody finished
    draw: bool
    finished: list[bool]
    ticks: list[int | None]  # tick each dot reached the exit, None if it did not
    seconds: list[float | None]
    total_ticks: int
    log: list[list[int]]  # one [action0, action1] per tick, for replay


class Race:
    def __init__(self, level: Level, window: int = DEFAULT_WINDOW, obs_version: int = OBS_VERSION):
        self.level = level
        self.window = window
        self.obs_version = obs_version
        # per dot: the last move and whether it bumped (shown to version 2 brains)
        self.last_moves: list[int | None] = [None, None]
        self.bumps = [False, False]
        self.step_limit = level.step_limit
        self.positions = [level.start, level.start]
        # visit count per square, one map per dot (as in MazeEnv: a bump counts again)
        self.visits: list[dict[tuple[int, int], int]] = [{level.start: 1}, {level.start: 1}]
        self.finish_tick: list[int | None] = [None, None]
        self.log: list[list[int]] = []
        self.tick_count = 0

    @property
    def over(self) -> bool:
        return any(t is not None for t in self.finish_tick) or self.tick_count >= self.step_limit

    def observation(self, dot: int) -> np.ndarray:
        return observe(
            self.level,
            self.positions[dot],
            self.visits[dot],
            self.window,
            self.obs_version,
            self.last_moves[dot],
            self.bumps[dot],
        )

    def tick(self, actions: Sequence[int]) -> None:
        if self.over:
            raise RuntimeError("the race is over")
        self.tick_count += 1
        for dot in (0, 1):
            self.positions[dot], bumped = move(self.level, self.positions[dot], int(actions[dot]))
            self.last_moves[dot] = int(actions[dot])
            self.bumps[dot] = bumped
            square = self.positions[dot]
            self.visits[dot][square] = self.visits[dot].get(square, 0) + 1
            if self.positions[dot] == self.level.exit:
                self.finish_tick[dot] = self.tick_count
        self.log.append([int(actions[0]), int(actions[1])])

    def result(self) -> RaceResult:
        done = [t is not None for t in self.finish_tick]
        draw = all(done)
        winner = None
        if done[0] != done[1]:
            winner = 0 if done[0] else 1
        return RaceResult(
            winner=winner,
            draw=draw,
            finished=done,
            ticks=list(self.finish_tick),
            seconds=[None if t is None else t * TICK_SECONDS for t in self.finish_tick],
            total_ticks=self.tick_count,
            log=[list(a) for a in self.log],
        )

    def run(self, brains: Sequence[Brain]) -> RaceResult:
        while not self.over:
            self.tick([brains[0](self.observation(0)), brains[1](self.observation(1))])
        return self.result()
