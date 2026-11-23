"""Pick the official brain on VALIDATION only: python scripts/research/official_select.py

For every seed under runs/official-dqn-shaped/ (official_train.sh), plays the exported brain on the
validation mazes and ranks by success, then fewer mean steps. The test mazes are never played here,
so they cannot influence the choice. Prints one JSON row per seed, then the winner.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, SCORE_TIME_LIMIT_S, play, summarise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=ROOT / "runs" / "official-dqn-shaped")
    args = parser.parse_args()

    from minotaurus.brain import load_brain
    from minotaurus.trainer.config import ConfigFile

    rows = []
    for seed_dir in sorted(args.runs.glob("s[0-9]*")):
        run = next(seed_dir.glob("*/*/brain.onnx")).parent
        config = ConfigFile.model_validate_json((run / "config.json").read_text())
        pools = config.resolve_pools()
        brain = load_brain(run / "brain.onnx", time_limit_s=SCORE_TIME_LIMIT_S)
        val = summarise([play(brain, level) for level in pools.validation])
        metrics = [json.loads(t) for t in (run / "metrics.jsonl").read_text().splitlines()]
        kept = [row for row in metrics if "exported_episode" in row][-1]
        ratio = val["ratio_finished"]
        rows.append(
            {
                "seed": config.seed,
                "run": str(run.relative_to(ROOT)) if run.is_relative_to(ROOT) else str(run),
                "val_success": val["success"],
                "val_mean_steps": round(val["mean_steps"], 2),
                "val_steps_ratio_finished": round(ratio, 3) if ratio is not None else None,
                "exported_episode": kept["exported_episode"],
            }
        )
    rows.sort(key=lambda r: (-r["val_success"], r["val_mean_steps"]))
    for row in rows:
        print(json.dumps(row))
    print("WINNER", json.dumps(rows[0]))


if __name__ == "__main__":
    main()
