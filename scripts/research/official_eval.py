"""Score the chosen brain only: python scripts/research/official_eval.py RUN_DIR

Run this after official_select.py has picked the brain. TEST success with policy_epsilon 0 and
0.05 (seeded per maze, as evaluate.py does), then one arena run (the server's run loop, seeded
as the server seeds it) on easy-01, easy-02, medium-01 and medium-02.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

LEVELS = ("easy-01", "easy-02", "medium-01", "medium-02")
TEST_EPSILONS = (0.0, 0.05)


async def arena_run(brain, level_id: str) -> dict:
    from minotaurus.brain import player
    from minotaurus.engine.levels import load_level_by_id
    from minotaurus.server.arena import run_arena

    level = load_level_by_id(level_id)
    mover = player(brain, seed=f"{getattr(brain, 'digest', '')}|{level.id}")  # as server/app.py
    last = None
    async for message in run_arena(level, mover, tick_seconds=0):
        last = message
    return {
        "level": level_id,
        "status": last.status,
        "steps": last.steps,
        "step_limit": level.step_limit,
        "message": getattr(last, "message", None),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()

    from minotaurus.brain import load_brain
    from minotaurus.trainer import evaluate
    from minotaurus.trainer.config import ConfigFile

    config = ConfigFile.model_validate_json((args.run_dir / "config.json").read_text())
    pools = config.resolve_pools()
    brain = load_brain(args.run_dir / "brain.onnx")
    for eps in TEST_EPSILONS:
        rate = evaluate.success_rate(brain, pools.test, policy_epsilon=eps)
        print(json.dumps({"split": "test", "policy_epsilon": eps, "success": rate}))
    for level_id in LEVELS:
        print(json.dumps({"arena": asyncio.run(arena_run(brain, level_id))}))


if __name__ == "__main__":
    main()
