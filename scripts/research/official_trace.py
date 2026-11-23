"""Trace a brain on the hand-made levels: python scripts/research/official_trace.py BRAIN.onnx

Headless, with the arena's player() and MazeEnv at each level's step limit. Per level: the shortest
path; the greedy run (finished or timeout, steps, bumps, the longest run of bumps in a row and where
it happened); the success rate with random moves when playing (policy_epsilon 0.05 and 0.1, 200
seeded tries each); and a greedy run that never picks a move into a wall it can see (play time
only, no retraining), with its steps and how often it revisits a square.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

EPSILONS = (0.05, 0.1)
TRIES = 200


def run(level, mover) -> dict:
    from minotaurus.engine import MazeEnv

    env = MazeEnv(level)
    obs, _ = env.reset()
    bumps = streak = 0
    worst = (0, None)
    visits = Counter([env.pos])
    done = finished = False
    while not done:
        before = env.pos
        obs, _, terminated, truncated, info = env.step(mover(obs))
        visits[env.pos] += 1
        if info["bumped"]:
            bumps += 1
            streak += 1
            if streak > worst[0]:
                worst = (streak, before)
        else:
            streak = 0
        finished, done = terminated, terminated or truncated
    return {
        "finished": finished,
        "steps": env.steps,
        "bumps": bumps,
        "max_bump_streak": worst[0],
        "bump_streak_at": worst[1],
        "most_visits": visits.most_common(2),
    }


def wall_blocked(brain, window: int = 5):
    """Greedy, but a move into a wall visible next to the dot is never chosen."""
    from minotaurus.engine.levels import MOVES

    half = window // 2

    def play(obs: np.ndarray) -> int:
        scores = np.array(brain.scores(obs), dtype=np.float64)
        for action, (dx, dy) in enumerate(MOVES):
            if obs[(half + dy) * window + (half + dx)] == 1.0:
                scores[action] = -np.inf
        return int(scores.argmax())

    return play


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brain", type=Path)
    args = parser.parse_args()

    from minotaurus.brain import load_brain, player
    from minotaurus.engine.levels import load_all_levels, shortest_path_length

    brain = load_brain(args.brain)
    for level in load_all_levels():
        row = {"level": level.id, "shortest": shortest_path_length(level)}
        row["step_limit"] = level.step_limit
        row["greedy"] = run(level, player(brain, seed=f"{brain.digest}|{level.id}", epsilon=0.0))
        for eps in EPSILONS:
            wins = 0
            for i in range(TRIES):
                mover = player(brain, seed=f"{brain.digest}|{level.id}|{i}", epsilon=eps)
                wins += run(level, mover)["finished"]
            row[f"eps_{eps}"] = wins / TRIES
        row["wall_blocked"] = run(level, wall_blocked(brain))
        print(json.dumps(row))


if __name__ == "__main__":
    main()
