"""Train one research run and score it: python scripts/research/run.py E 1 [--episodes N].

Writes <out>/<run>-s<seed>/: the training run (metrics.jsonl, training.png, config.json,
brain.onnx, checkpoints/) and result.json (evaluate.py success rates, step metrics on train,
validation and test, a seeded random player on test, training CPU seconds).
"""

from __future__ import annotations

import argparse
import functools
import json
import random
import resource
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DEFAULT_OUT, RUNS, SCORE_TIME_LIMIT_S, play, research_config, summarise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", choices=sorted(RUNS))
    parser.add_argument("seed", type=int)
    parser.add_argument("--episodes", type=int, default=5000)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    import torch

    from minotaurus.brain import load_brain
    from minotaurus.trainer import evaluate
    from minotaurus.trainer.config import ConfigFile
    from minotaurus.trainer.plot import plot_metrics
    from minotaurus.trainer.train import train

    torch.set_num_threads(1)  # one core per run when many run at once
    evaluate.load_brain = functools.partial(load_brain, time_limit_s=SCORE_TIME_LIMIT_S)

    config = ConfigFile.model_validate(research_config(args.run, args.seed, args.episodes))
    pools = config.resolve_pools()
    folder = args.out / f"{args.run}-s{args.seed}"
    run_dir = train(
        config,
        pools.train,
        run_dir=folder / "run",
        log_every=50,
        stages=config.resolve_stages(pools),
    )
    usage = resource.getrusage(resource.RUSAGE_SELF)
    train_cpu = usage.ru_utime + usage.ru_stime
    plot_metrics(run_dir / "metrics.jsonl", run_dir / "training.png", title=config.name)

    official = evaluate.score_brain(run_dir / "brain.onnx", config, pools)
    brain = load_brain(run_dir / "brain.onnx", time_limit_s=SCORE_TIME_LIMIT_S)
    result = {"run": args.run, "seed": args.seed, "train_cpu_s": round(train_cpu, 1)}
    result["official"] = official
    for split in ("train", "validation", "test"):
        rows = []
        for level in getattr(pools, split):
            rows.append(play(brain, level))
        result[split] = summarise(rows)
    rng = random.Random(1000 + args.seed)
    rows = []
    for level in pools.test:
        rows.append(play(brain, level, epsilon=1.0, rng=rng))
    result["random_player_test"] = summarise(rows)
    first = []
    for text in (run_dir / "metrics.jsonl").read_text().splitlines():
        line = json.loads(text)
        if "success_rate" in line and line["episode"] <= 500:
            first.append(line["success_rate"])
    result["first500_exit"] = sum(first) / len(first) if first else None
    (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"run": args.run, "seed": args.seed, "official": official}))


if __name__ == "__main__":
    main()
