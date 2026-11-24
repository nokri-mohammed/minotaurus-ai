"""Train one recipe with several seeds, several runs at the same time (one CPU core each)."""

from __future__ import annotations

import json
import multiprocessing
import os
import time
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.plot import plot_metrics, read_metrics
from minotaurus.trainer.summary import format_duration


@dataclass(frozen=True)
class SeedResult:
    seed: int
    run_dir: str
    seconds: float
    success_rate: float  # the last logging window of training
    avg_steps: float  # the same window
    avg_path_ratio: float | None
    scores: dict[str, float] | None  # train, validation, test: made mazes only
    fixed: dict[str, bool] | None = None  # hand-made levels finished: level id -> True or False


def default_parallel(n_seeds: int) -> int:
    """One run per CPU core, but never more runs than seeds.

    Example: 8 seeds on a 4-core PC -> 4; 2 seeds on a 4-core PC -> 2.
    """
    cores = os.cpu_count() or 1
    return max(1, min(n_seeds, cores))


def train_one_seed(config_data: dict, run_dir: str, log_every: int, plot: bool) -> SeedResult:
    """Train one seed. Runs in its own process, so it takes plain data and returns plain data."""
    from minotaurus.trainer.train import train

    config = ConfigFile.model_validate(config_data)
    pools = config.resolve_pools()
    levels = pools.train if pools is not None else config.resolve_levels()
    stages = config.resolve_stages(pools)
    started = time.monotonic()
    done_dir = train(
        config, levels, run_dir=run_dir, log_every=log_every, pools=pools, stages=stages
    )
    seconds = time.monotonic() - started
    last = None
    for row in read_metrics(done_dir / "metrics.jsonl"):
        if "avg_steps" in row:
            last = row
    scores = None
    scores_file = done_dir / "scores.json"
    if scores_file.exists():
        scores = json.loads(scores_file.read_text())
    fixed = None
    fixed_file = done_dir / "fixed_levels.json"
    if fixed_file.exists():
        fixed = json.loads(fixed_file.read_text())
    if plot:
        plot_metrics(done_dir / "metrics.jsonl", done_dir / "training.png", title=config.name)
    if last is None:
        raise RuntimeError(f"seed {config.seed}: training wrote no metrics")
    return SeedResult(
        seed=config.seed,
        run_dir=str(done_dir),
        seconds=seconds,
        success_rate=last["success_rate"],
        avg_steps=last["avg_steps"],
        avg_path_ratio=last.get("avg_path_ratio"),
        scores=scores,
        fixed=fixed,
    )


def run_seeds(
    config: ConfigFile,
    seeds: list[int],
    parallel: int,
    base_dir: str | Path,
    log_every: int = 10,
    plot: bool = True,
) -> Iterator[SeedResult]:
    """Train `config` once per seed, `parallel` at a time. Yields each result as it finishes.

    Seed N is written to base_dir/seed-N/. Results come in the order the runs end, not seed order.
    """
    base_dir = Path(base_dir)
    context = multiprocessing.get_context("spawn")  # a fresh process each: safe with torch
    with ProcessPoolExecutor(max_workers=parallel, mp_context=context) as pool:
        pending = []
        for seed in seeds:
            data = json.loads(config.for_seed(seed).model_dump_json(exclude_unset=True))
            run_dir = str(base_dir / f"seed-{seed}")
            pending.append(pool.submit(train_one_seed, data, run_dir, log_every, plot))
        for future in as_completed(pending):
            yield future.result()


def _selection_score(result: SeedResult) -> float:
    """What picks the best seed: the validation score; without made mazes, the last success rate.

    The test score is never used here, so the test mazes stay unseen when choosing.
    """
    if result.scores is not None:
        return result.scores["validation"]
    return result.success_rate


def _is_better(candidate: SeedResult, best: SeedResult) -> bool:
    if _selection_score(candidate) != _selection_score(best):
        return _selection_score(candidate) > _selection_score(best)
    if candidate.avg_steps != best.avg_steps:
        return candidate.avg_steps < best.avg_steps
    return candidate.seed < best.seed


def pick_best(results: list[SeedResult]) -> SeedResult:
    """The best seed: highest validation score, then fewer steps, then the lower seed."""
    best = results[0]
    for result in results[1:]:
        if _is_better(result, best):
            best = result
    return best


def _percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.0%}"


def results_table(results: list[SeedResult], best: SeedResult) -> list[str]:
    """One line per seed, in seed order, with a trophy on the best one."""
    lines = ["seed   finished  validation  test   hand-made  steps  path   time"]
    for result in sorted(results, key=lambda r: r.seed):
        validation = None
        test = None
        if result.scores is not None:
            validation = result.scores["validation"]
            test = result.scores["test"]
        ratio = "-"
        if result.avg_path_ratio is not None:
            ratio = f"{result.avg_path_ratio:.2f}"
        hand_made = "-"
        if result.fixed is not None:
            done = 0
            for finished in result.fixed.values():
                if finished:
                    done += 1
            hand_made = f"{done}/{len(result.fixed)}"
        mark = "🏆" if result.seed == best.seed else "  "
        lines.append(
            f"{mark}{result.seed:<4} {_percent(result.success_rate):<9} {_percent(validation):<11}"
            f" {_percent(test):<6} {hand_made:<10} {result.avg_steps:<6.1f} {ratio:<6} "
            f"{format_duration(result.seconds)}"
        )
    return lines
