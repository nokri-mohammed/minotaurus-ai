"""Shared helpers for the research scripts. Paths are relative to the repository root."""

from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "data" / "examples"
DEFAULT_OUT = ROOT / "runs" / "research"  # runs/ is git-ignored: results are never committed

# The loader's per-step limit is 0.05 s. Many runs at once share the CPU, so the research scored
# with 1 s. Scoring only; the repo default does not change.
SCORE_TIME_LIMIT_S = 1.0

POOLS = {
    "A": {"size": 9, "maze_seed": 1, "train": 222, "validation": 50, "test": 50},
    "B": {"size": 11, "maze_seed": 1, "train": 222, "validation": 100, "test": 100},
    "C": {"size": 11, "maze_seed": 1, "train": 500, "validation": 100, "test": 100},
}

# Every run of 2026-11-23 (docs/research/2026-11-23-dqn-shaping.md). The research exported the
# last brain, so eval_every is 0 here; checkpoint_sweep.py picks the best one afterwards.
RUNS = {
    "A": {"pools": "A"},
    "B": {"pools": "B"},
    "C": {"pools": "C"},
    "D": {"pools": "A", "train_step_limit_factor": 20.0, "epsilon_decay": 0.999},
    "E": {"pools": "A", "shaping": True},
    "F": {"pools": "A", "shaping": True, "train_step_limit_factor": 20.0, "epsilon_decay": 0.999},
    "G": {
        "pools": "A",
        "shaping": True,
        "train_step_limit_factor": 20.0,
        "epsilon_decay": 0.999,
        "stages": [5, 7, 9],
    },
    "E11": {"pools": "B", "shaping": True},
    "Enb": {"pools": "A", "shaping": True, "shaping_on_bump": False},
}


def research_config(run: str, seed: int, episodes: int = 5000) -> dict:
    """The config (as a dict) of one research run: dqn-brain.json plus the run's options."""
    options = RUNS[run]
    data = json.loads((EXAMPLES / "dqn-brain.json").read_text())
    data["name"] = f"dqn-{run}-s{seed}"
    data["seed"] = seed
    data["episodes"] = episodes
    data["levels"] = {"generated": dict(POOLS[options["pools"]])}
    data["eval_every"] = 0
    if "epsilon_decay" in options:
        data["dqn"]["epsilon_decay"] = options["epsilon_decay"]
    if options.get("shaping"):
        data["dqn"]["shaping"] = True
        data["dqn"]["shaping_on_bump"] = options.get("shaping_on_bump", True)
    if "train_step_limit_factor" in options:
        data["train_step_limit_factor"] = options["train_step_limit_factor"]
    if "stages" in options:
        data["stages"] = options["stages"]
    return data


def play(brain, level, epsilon: float = 0.0, rng: random.Random | None = None) -> dict:
    """One scored episode at the level's own step limit, with an optional random-move rate.

    Returns finished, steps, steps / shortest path, ties (steps where the top score was shared),
    bumps, and looped (the same position and view seen 3 or more times).
    """
    from minotaurus.engine import MazeEnv
    from minotaurus.engine.levels import shortest_path_length

    env = MazeEnv(level)
    obs, _ = env.reset()
    seen = Counter()
    done = finished = False
    steps = ties = bumps = 0
    while not done:
        seen[(env.pos, obs.tobytes())] += 1
        if rng is not None and rng.random() < epsilon:
            action = rng.randrange(4)
        else:
            scores = brain.scores(obs)
            action = int(scores.argmax())
            if (scores == scores.max()).sum() > 1:
                ties += 1
        obs, _, terminated, truncated, info = env.step(action)
        bumps += info["bumped"]
        steps += 1
        finished, done = terminated, terminated or truncated
    return {
        "finished": finished,
        "steps": steps,
        "ratio": steps / shortest_path_length(level),
        "ties": ties,
        "bumps": bumps,
        "looped": max(seen.values()) >= 3,
    }


def summarise(rows: list[dict]) -> dict:
    """Success, mean steps, steps / shortest (all and finished), tie, bump and loop shares."""
    finished = []
    for row in rows:
        if row["finished"]:
            finished.append(row)
    steps = 0
    ratio_all = ratio_done = ties = bumps = 0.0
    failed = looped = 0
    for row in rows:
        steps += row["steps"]
        ratio_all += row["ratio"]
        ties += row["ties"]
        bumps += row["bumps"]
        if not row["finished"]:
            failed += 1
            looped += row["looped"]
    for row in finished:
        ratio_done += row["ratio"]
    return {
        "success": len(finished) / len(rows),
        "mean_steps": steps / len(rows),
        "ratio_all": ratio_all / len(rows),
        "ratio_finished": ratio_done / len(finished) if finished else None,
        "tie_steps": ties / steps,
        "bump_steps": bumps / steps,
        "loop_rate": looped / failed if failed else None,
    }
