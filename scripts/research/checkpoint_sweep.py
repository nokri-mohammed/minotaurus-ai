"""Score every saved checkpoint of a DQN run on validation, keep the best, score it on test.

python scripts/research/checkpoint_sweep.py runs/research/F-s2/run
Writes sweep.json and the best checkpoint as best-ep<N>.onnx next to the run folder.
A tie keeps the later checkpoint, as the trainer's best-on-validation export does.
"""

from __future__ import annotations

import argparse
import functools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SCORE_TIME_LIMIT_S, play, summarise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()

    import torch

    from minotaurus.brain import load_brain
    from minotaurus.trainer import evaluate
    from minotaurus.trainer.config import ConfigFile
    from minotaurus.trainer.evaluate import POOLS_KEY
    from minotaurus.trainer.export import export_dqn
    from minotaurus.trainer.train import make_agent

    torch.set_num_threads(1)
    evaluate.load_brain = functools.partial(load_brain, time_limit_s=SCORE_TIME_LIMIT_S)
    config = ConfigFile.model_validate_json((args.run_dir / "config.json").read_text())
    pools = config.resolve_pools()
    meta = {POOLS_KEY: json.dumps(config.pool_settings(), sort_keys=True)}
    out = args.run_dir.parent
    checks = []
    for path in sorted((args.run_dir / "checkpoints").glob("ep*.pt")):
        episode = int(path.stem[2:])
        agent = make_agent(config)
        agent.net.load_state_dict(torch.load(path))
        onnx_path = out / f"ep{episode}.onnx"
        export_dqn(agent, onnx_path, config.name, [], config.window, meta)
        val = evaluate.success_rate(evaluate.load_brain(onnx_path), pools.validation)
        checks.append({"episode": episode, "validation": val, "path": onnx_path})
    if not checks:
        sys.exit(f"no checkpoints in {args.run_dir / 'checkpoints'} (saved every 500 tries)")
    best = checks[0]
    for check in checks:
        if check["validation"] >= best["validation"]:  # a tie keeps the later checkpoint
            best = check
    brain = load_brain(best["path"], time_limit_s=SCORE_TIME_LIMIT_S)
    result = {"best_episode": best["episode"], "checks": []}
    for check in checks:
        result["checks"].append({"episode": check["episode"], "validation": check["validation"]})
    for split in ("validation", "test"):
        rows = []
        for level in getattr(pools, split):
            rows.append(play(brain, level))
        result[split] = summarise(rows)
    for check in checks:
        if check is not best:
            check["path"].unlink()
    best["path"].rename(out / f"best-ep{best['episode']}.onnx")
    (out / "sweep.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"best_episode": best["episode"], "test": result["test"]["success"]}))


if __name__ == "__main__":
    main()
