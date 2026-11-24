"""Train one recipe with several seeds, several runs at the same time (one CPU core each)."""

from __future__ import annotations

import json
import multiprocessing
import os
import queue
import time
from collections.abc import Iterator
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
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
    # The saved brain (not the last training window):
    saved_at: int | None = None  # the try the saved brain came from
    saved_validation: float | None = None  # its validation score when it was saved
    final_validation: float | None = None  # the validation check at the end of training
    test_steps: float | None = None  # average steps on the test mazes
    test_path_ratio: float | None = None  # average path ratio on the test mazes (finished only)


def default_parallel(n_seeds: int) -> int:
    """One run per CPU core, but never more runs than seeds.

    Example: 8 seeds on a 4-core PC -> 4; 2 seeds on a 4-core PC -> 2.
    """
    cores = os.cpu_count() or 1
    return max(1, min(n_seeds, cores))


def train_one_seed(
    config_data: dict, run_dir: str, log_every: int, plot: bool, progress_queue=None
) -> SeedResult:
    """Train one seed. Runs in its own process, so it takes plain data and returns plain data.

    With a `progress_queue`, it puts (seed, tries done) on it at every logging window.
    """
    from minotaurus.trainer.train import train

    config = ConfigFile.model_validate(config_data)
    pools = config.resolve_pools()
    levels = pools.train if pools is not None else config.resolve_levels()
    stages = config.resolve_stages(pools)

    def report(line: dict) -> None:
        progress_queue.put((config.seed, line["episode"]))

    progress = None
    if progress_queue is not None:
        progress = report
    started = time.monotonic()
    done_dir = train(
        config,
        levels,
        run_dir=run_dir,
        log_every=log_every,
        progress=progress,
        pools=pools,
        stages=stages,
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
    saved_at = None
    saved_validation = None
    final_validation = None
    for row in read_metrics(done_dir / "metrics.jsonl"):
        if "exported_episode" in row:
            saved_at = row["exported_episode"]
            saved_validation = row["validation_success"]
        elif "validation_success" in row:
            final_validation = row["validation_success"]  # the last check wins
    test_stats = None
    stats_file = done_dir / "test_stats.json"
    if stats_file.exists():
        test_stats = json.loads(stats_file.read_text())
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
        saved_at=saved_at,
        saved_validation=saved_validation,
        final_validation=final_validation,
        test_steps=test_stats["avg_steps"] if test_stats is not None else None,
        test_path_ratio=test_stats["avg_path_ratio"] if test_stats is not None else None,
    )


def _drain(progress_queue, on_progress) -> None:
    """Hand every waiting (seed, tries) message to `on_progress`."""
    while True:
        try:
            seed, episode = progress_queue.get_nowait()
        except queue.Empty:
            return
        on_progress(seed, episode)


def run_seeds(
    config: ConfigFile,
    seeds: list[int],
    parallel: int,
    base_dir: str | Path,
    log_every: int = 10,
    plot: bool = True,
    on_progress=None,
) -> Iterator[SeedResult]:
    """Train `config` once per seed, `parallel` at a time. Yields each result as it finishes.

    Seed N is written to base_dir/seed-N/. Results come in the order the runs end, not seed order.
    With `on_progress(seed, tries_done)`, it is called while the runs go on, at every logging
    window of every seed (from this process, so it can print).
    """
    base_dir = Path(base_dir)
    context = multiprocessing.get_context("spawn")  # a fresh process each: safe with torch
    manager = None
    progress_queue = None
    if on_progress is not None:
        manager = context.Manager()  # the workers are other processes: they need a shared queue
        progress_queue = manager.Queue()
    try:
        with ProcessPoolExecutor(max_workers=parallel, mp_context=context) as pool:
            pending = []
            for seed in seeds:
                data = json.loads(config.for_seed(seed).model_dump_json(exclude_unset=True))
                run_dir = str(base_dir / f"seed-{seed}")
                pending.append(
                    pool.submit(train_one_seed, data, run_dir, log_every, plot, progress_queue)
                )
            waiting = set(pending)
            while waiting:
                finished, waiting = wait(waiting, timeout=0.5, return_when=FIRST_COMPLETED)
                if progress_queue is not None:
                    _drain(progress_queue, on_progress)
                for future in finished:
                    yield future.result()
    finally:
        if manager is not None:
            manager.shutdown()


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
    """One line per seed, in seed order, with a trophy on the best one.

    "saved at" is the try the saved brain came from. With made mazes, "steps" and "path" are how
    the saved brain plays the test mazes; without them they are the last training window.
    """
    lines = ["seed   saved at   validation  test   hand-made  steps  path   time"]
    for result in sorted(results, key=lambda r: r.seed):
        validation = None
        test = None
        if result.scores is not None:
            validation = result.scores["validation"]
            test = result.scores["test"]
        saved = "-"
        if result.saved_at is not None:
            saved = f"try {result.saved_at}"
        steps = result.avg_steps
        path_ratio = result.avg_path_ratio
        if result.test_steps is not None:
            steps = result.test_steps
            path_ratio = result.test_path_ratio
        ratio = "-"
        if path_ratio is not None:
            ratio = f"{path_ratio:.2f}"
        hand_made = "-"
        if result.fixed is not None:
            done = 0
            for finished in result.fixed.values():
                if finished:
                    done += 1
            hand_made = f"{done}/{len(result.fixed)}"
        mark = "🏆" if result.seed == best.seed else "  "
        lines.append(
            f"{mark}{result.seed:<4} {saved:<10} {_percent(validation):<11}"
            f" {_percent(test):<6} {hand_made:<10} {steps:<6.1f} {ratio:<6} "
            f"{format_duration(result.seconds)}"
        )
    return lines


def collapse_warnings(results: list[SeedResult]) -> list[str]:
    """One line for each seed whose last validation check fell below half of its saved brain's.

    It means training got worse after the saved try (a collapse), so the saved brain is an early one.
    """
    lines = []
    for result in sorted(results, key=lambda r: r.seed):
        saved = result.saved_validation
        final = result.final_validation
        if saved is None or final is None or saved <= 0:
            continue
        if final < saved / 2:
            lines.append(
                f"⚠️  seed {result.seed}: training collapsed after the saved brain "
                f"(validation {_percent(saved)} at try {result.saved_at}, "
                f"{_percent(final)} at the end)"
            )
    return lines
