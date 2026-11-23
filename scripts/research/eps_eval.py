"""Score a trained brain with test-time random-move rates, seeded, several repeats.

python scripts/research/eps_eval.py runs/research/E-s1/run --name E-s1
Writes <run>/../eps.json: one row per (rate, repeat, split) with success, steps / shortest on
finished mazes and the loop rate of failed episodes.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SCORE_TIME_LIMIT_S, play, summarise

RATES = (0.0, 0.02, 0.05, 0.1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--name", required=True, help="seeds the random moves, e.g. E-s1")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()

    from minotaurus.brain import load_brain
    from minotaurus.trainer.config import ConfigFile

    config = ConfigFile.model_validate_json((args.run_dir / "config.json").read_text())
    pools = config.resolve_pools()
    brain = load_brain(args.run_dir / "brain.onnx", time_limit_s=SCORE_TIME_LIMIT_S)
    rows = []
    for rate in RATES:
        for repeat in range(args.repeats):
            rng = random.Random(f"{args.name}|{rate}|{repeat}")  # a str seed is repeatable
            for split in ("validation", "test"):
                episodes = []
                for level in getattr(pools, split):
                    episodes.append(play(brain, level, epsilon=rate, rng=rng))
                row = {"brain": args.name, "eps": rate, "repeat": repeat, "split": split}
                row.update(summarise(episodes))
                rows.append(row)
    (args.run_dir.parent / "eps.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(f"{args.name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
