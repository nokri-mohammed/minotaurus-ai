"""Score a trained brain on mazes. The brain must come from the same pools as the config."""

from __future__ import annotations

import json
from pathlib import Path

from minotaurus.brain import Brain, load_brain, player
from minotaurus.engine import MazeEnv
from minotaurus.engine.levels import Level, LevelError, load_all_levels, shortest_path_length
from minotaurus.engine.pools import Pools
from minotaurus.trainer.config import ConfigFile

POOLS_KEY = "pools"  # the .onnx metadata key that holds the generated-maze settings


def finishes(brain: Brain, level: Level) -> bool:
    """Run the brain once on a maze. True if it reaches the exit before the step limit."""
    env = MazeEnv(level)
    obs, _ = env.reset()
    done = False
    reached = False
    while not done:
        obs, _, terminated, truncated, _ = env.step(brain(obs))
        reached = terminated
        done = terminated or truncated
    return reached


def success_rate(
    brain: Brain,
    levels: tuple[Level, ...],
    seed: int | str = 0,
    policy_epsilon: float | None = None,
) -> float:
    """Share of the mazes the brain finishes, from 0.0 to 1.0.

    A brain with policy_epsilon (or `policy_epsilon` given here) makes that share of its moves at
    random, seeded per maze from `seed` and the maze id, so the score can be repeated.
    """
    done = 0
    for level in levels:
        mover = player(brain, seed=f"{seed}|{level.id}", epsilon=policy_epsilon)
        if finishes(mover, level):
            done += 1
    return done / len(levels)


def score_brain(
    path: Path,
    config: ConfigFile,
    pools: Pools | None = None,
    policy_epsilon: float | None = None,
) -> dict[str, float]:
    """Success rate on the train, validation and test mazes.

    The brain plays with its own policy_epsilon (random-move rate) unless `policy_epsilon` is given.
    Raises LevelError when the config has no generated mazes, or the brain was trained on other
    ones (its metadata differs from the config), so a score is never taken on the wrong test.
    """
    expected = config.pool_settings()
    if expected is None:
        raise LevelError("this config has no generated mazes to score on")
    brain = load_brain(path)
    saved = json.loads(brain.meta.get(POOLS_KEY, "null"))
    if saved != expected:
        raise LevelError("this brain was trained on different mazes than the config names")
    if pools is None:
        pools = config.resolve_pools()
    if pools is None:
        raise LevelError("this config has no generated mazes to score on")
    return {
        "train": success_rate(brain, pools.train, policy_epsilon=policy_epsilon),
        "validation": success_rate(brain, pools.validation, policy_epsilon=policy_epsilon),
        "test": success_rate(brain, pools.test, policy_epsilon=policy_epsilon),
    }


def score_fixed_levels(path: Path) -> dict[str, bool]:
    """Does the brain finish each hand-made level (easy-01 to hard-02)? Level id -> True or False.

    An extra check on mazes of other sizes and styles than the made ones. It is never used to
    choose a brain: validation does that.
    """
    brain = load_brain(path)
    results = {}
    for level in load_all_levels():
        mover = player(brain, seed=f"fixed|{level.id}")
        results[level.id] = finishes(mover, level)
    return results


def playthrough_stats(
    path: Path, levels: tuple[Level, ...], policy_epsilon: float | None = None
) -> dict[str, float | None]:
    """How the saved brain plays `levels` (the test mazes): average steps over every try, and the
    average path ratio (steps / shortest path) over the tries it finished.

    avg_path_ratio is None when it finished none. It plays the same way as success_rate, so the
    numbers match the test score.
    """
    brain = load_brain(path)
    total_steps = 0
    total_ratio = 0.0
    finished = 0
    for level in levels:
        mover = player(brain, seed=f"0|{level.id}", epsilon=policy_epsilon)
        env = MazeEnv(level)
        obs, _ = env.reset()
        done = False
        reached = False
        steps = 0
        while not done:
            obs, _, terminated, truncated, _ = env.step(mover(obs))
            steps += 1
            reached = terminated
            done = terminated or truncated
        total_steps += steps
        if reached:
            finished += 1
            total_ratio += steps / shortest_path_length(level)
    ratio = None
    if finished > 0:
        ratio = round(total_ratio / finished, 3)
    return {"avg_steps": round(total_steps / len(levels), 1), "avg_path_ratio": ratio}
