"""The run loop: one brain on one level, one move per tick, as a stream of messages."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from minotaurus.brain import BrainError
from minotaurus.engine import MazeEnv
from minotaurus.engine.levels import Level, shortest_path_length
from minotaurus.engine.race import TICK_SECONDS, Brain
from minotaurus.server.messages import ErrorMessage, Point, Result, RunStarted, Tick

N_ACTIONS = 4


def _game_seconds(steps: int) -> float:
    """Game time: every tick is 0.1 s of game time, however fast the server really runs."""
    return round(steps * TICK_SECONDS, 1)


async def run_arena(
    level: Level, brain: Brain, tick_seconds: float = TICK_SECONDS
) -> AsyncIterator[RunStarted | Tick | Result | ErrorMessage]:
    """Run `brain` on `level`. Yields run_started, then one tick per move, then one result.

    The run ends when the dot reaches the exit (finished), when the level's step limit is used up
    (timed_out), or when the brain fails (error). `tick_seconds` is the real pause between ticks;
    tests pass 0 to run fast. The brain is untrusted, so anything it raises ends the run cleanly.
    """
    env = MazeEnv(level)
    obs, _ = env.reset()
    start_x, start_y = level.start
    yield RunStarted(
        type="run_started",
        level_id=level.id,
        start=Point(x=start_x, y=start_y),
        step_limit=level.step_limit,
    )

    steps = 0
    while True:
        await asyncio.sleep(tick_seconds)

        try:
            action = brain(obs)
            if action < 0 or action >= N_ACTIONS:
                raise BrainError(f"the brain chose move {action}, but moves are 0 to 3")
        except Exception as exc:  # noqa: BLE001  the brain is untrusted: whatever it raises ends the run
            yield Result(
                type="result",
                status="error",
                steps=steps,
                seconds=_game_seconds(steps),
                message=str(exc),
            )
            return

        obs, _reward, terminated, truncated, info = env.step(action)
        steps += 1
        x, y = info["pos"]
        yield Tick(type="tick", n=steps, x=x, y=y)

        if terminated:
            yield Result(
                type="result",
                status="finished",
                steps=steps,
                seconds=_game_seconds(steps),
                path_ratio=round(steps / shortest_path_length(level), 2),
            )
            return
        if truncated:
            yield Result(
                type="result", status="timed_out", steps=steps, seconds=_game_seconds(steps)
            )
            return
