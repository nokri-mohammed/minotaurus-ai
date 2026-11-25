"""`minotaurus train --config <file>`."""

import json
import shutil
import sys
import time
from pathlib import Path
from typing import Annotated

import typer


def run(
    config: Annotated[
        Path, typer.Option(help="Path to a brain config .json.", exists=True, dir_okay=False)
    ],
    runs_dir: Annotated[str, typer.Option(help="Where runs are written.")] = "runs",
    log_every: Annotated[int, typer.Option(help="Episodes per metrics line.")] = 10,
    plot: Annotated[
        bool, typer.Option("--plot/--no-plot", help="Draw training.png when training ends.")
    ] = True,
    seeds: Annotated[
        int | None,
        typer.Option(
            min=1,
            help="Train this many seeds, counting up from the config seed. Overrides config seeds.",
        ),
    ] = None,
    parallel: Annotated[
        int | None,
        typer.Option(min=1, help="Runs at the same time. Default: one per CPU core."),
    ] = None,
) -> None:
    from pydantic import ValidationError

    from minotaurus.bundle import build_bundle
    from minotaurus.engine.levels import LevelError
    from minotaurus.signing import existing_default_key
    from minotaurus.trainer.config import ConfigFile
    from minotaurus.trainer.plot import plot_metrics, read_metrics
    from minotaurus.trainer.progress import single_line
    from minotaurus.trainer.summary import summarize_run
    from minotaurus.trainer.train import train

    try:
        # Read the JSON file and build a checked ConfigFile; a wrong setting raises an error
        # that names it. `loaded` is the parsed object: loaded.name, loaded.episodes, ...
        loaded = ConfigFile.model_validate_json(config.read_text())
        # The level ids must exist on disk (the settings check cannot know that). Keep the
        # result: train() uses these same levels, so the files are read only once.
        # Generated mazes come as pools (train, validation, test); other shapes have no pools.
        pools = loaded.resolve_pools()
        levels = pools.train if pools is not None else loaded.resolve_levels()
        # Experimental curriculum: smaller practice mazes first (None without "stages").
        stages = loaded.resolve_stages(pools)
    except (ValidationError, LevelError) as exc:
        typer.echo(f"minotaurus: bad config:\n{exc}", err=True)
        raise typer.Exit(2) from exc

    from minotaurus.signing import signing_notice

    typer.echo(signing_notice())  # before training starts, so a missing key is seen at once

    # Several seeds: from --seeds N, or from "seeds" in the config. Neither: one run, as before.
    seed_values = None
    if seeds is not None:
        seed_values = []
        for step in range(seeds):
            seed_values.append(loaded.seed + step)
    elif loaded.seeds is not None:
        seed_values = loaded.seeds
    if seed_values is not None:
        _train_many(loaded, seed_values, parallel, runs_dir, log_every, plot)
        return

    # On a terminal: one line that redraws in place (bar, percent, time left). On a pipe or a
    # file: the plain line per window, so logs stay readable.
    live = sys.stdout.isatty()
    started = time.monotonic()

    def show(line: dict) -> None:
        if live:
            text = single_line(
                line["episode"],
                loaded.episodes,
                time.monotonic() - started,
                line["success_rate"],
                shutil.get_terminal_size().columns,
            )
            typer.echo(f"\r\x1b[K{text}", nl=False)
            return
        typer.echo(
            f"episode {line['episode']}/{loaded.episodes}  reward {line['avg_reward']:.3f}  "
            f"steps {line['avg_steps']:.1f}  success {line['success_rate']:.0%}  "
            f"epsilon {line['epsilon']:.3f}"
        )

    run_dir = train(
        loaded, levels, runs_dir, log_every=log_every, progress=show, pools=pools, stages=stages
    )
    if live:
        typer.echo("")  # leave the progress line and go to a new one
    seconds = time.monotonic() - started
    typer.echo(f"\n{typer.style('brain written:', bold=True)} {run_dir / 'brain.onnx'}")
    # Best brain on validation (G4): the last metrics line says which brain was kept.
    for row in read_metrics(run_dir / "metrics.jsonl"):
        if "exported_episode" in row:
            typer.echo(
                f"exported the brain from episode {row['exported_episode']} "
                f"(validation {row['validation_success']:.0%})"
            )
            if "stopped_at_episode" in row:
                typer.echo(
                    f"stopped early at try {row['stopped_at_episode']} "
                    f"(no better validation in {loaded.patience} checks)"
                )
            if "warning" in row:
                typer.echo(f"warning: {row['warning']}")
    scores_file = run_dir / "scores.json"
    if scores_file.exists():
        scores = json.loads(scores_file.read_text())
        typer.echo(
            f"finished mazes: train {scores['train']:.0%}  "
            f"validation {scores['validation']:.0%}  test {scores['test']:.0%}"
        )
    fixed_file = run_dir / "fixed_levels.json"
    if fixed_file.exists():
        fixed = json.loads(fixed_file.read_text())
        typer.echo(f"hand-made levels: {_fixed_text(fixed)}")
    if plot:
        graph = plot_metrics(run_dir / "metrics.jsonl", run_dir / "training.png", title=loaded.name)
        typer.echo(f"{typer.style('graph written:', bold=True)} {graph}")
    for text in summarize_run(run_dir, seconds):
        typer.echo(text)
    key = existing_default_key()
    bundle_path = build_bundle(run_dir, signing_key=key)
    signed = "  (signed)" if key is not None else ""
    typer.echo(f"{typer.style('bundle written:', bold=True)} {bundle_path}{signed}")
    typer.echo(f"\n✅ Done. Your brain: {run_dir / 'brain.onnx'}")


def _train_many(loaded, seed_values, parallel, runs_dir, log_every, plot) -> None:
    """Several seeds at once: one folder per seed, the best brain copied next to them."""
    import os
    from datetime import datetime

    from minotaurus.trainer.multi import (
        collapse_warnings,
        default_parallel,
        pick_best,
        results_table,
        run_seeds,
        table_note,
    )
    from minotaurus.trainer.progress import multi_line
    from minotaurus.trainer.summary import format_duration

    how_many = parallel or loaded.parallel or default_parallel(len(seed_values))
    base_dir = Path(runs_dir) / loaded.name / datetime.now().strftime("%Y%m%d-%H%M%S")
    typer.echo(
        f"Training {len(seed_values)} seeds, {how_many} at a time "
        f"(this PC has {os.cpu_count()} CPU cores)."
    )
    live = sys.stdout.isatty()
    started = time.monotonic()
    results = []
    tries = {}
    for seed in seed_values:
        tries[seed] = 0

    def redraw() -> None:
        text = multi_line(
            tries,
            loaded.episodes,
            len(results),
            time.monotonic() - started,
            shutil.get_terminal_size().columns,
        )
        typer.echo(f"\r\x1b[K{text}", nl=False)

    def on_progress(seed: int, episode: int) -> None:
        tries[seed] = episode
        redraw()

    on_update = None
    if live:
        on_update = on_progress
    for result in run_seeds(loaded, seed_values, how_many, base_dir, log_every, plot, on_update):
        results.append(result)
        tries[result.seed] = loaded.episodes
        if live:
            typer.echo("\r\x1b[K", nl=False)  # clear the bar, print the line, draw the bar again
        typer.echo(f"  seed {result.seed} done: {len(results)}/{len(seed_values)}")
        if live and len(results) < len(seed_values):
            redraw()
    seconds = time.monotonic() - started
    best = pick_best(results)
    best_brain = base_dir / "best-brain.onnx"
    shutil.copy2(Path(best.run_dir) / "brain.onnx", best_brain)
    best_bundle = base_dir / "best-bundle.tar"
    shutil.copy2(Path(best.run_dir) / "bundle.tar", best_bundle)
    rows = []
    for result in sorted(results, key=lambda r: r.seed):
        rows.append(
            {
                "seed": result.seed,
                "run_dir": result.run_dir,
                "seconds": round(result.seconds, 1),
                "success_rate": result.success_rate,
                "avg_steps": result.avg_steps,
                "avg_path_ratio": result.avg_path_ratio,
                "scores": result.scores,
                "fixed_levels": result.fixed,
                "saved_at": result.saved_at,
                "tries_done": result.tries_done,
                "saved_validation": result.saved_validation,
                "final_validation": result.final_validation,
                "test_steps": result.test_steps,
                "test_path_ratio": result.test_path_ratio,
            }
        )
    summary = {"best_seed": best.seed, "seconds": round(seconds, 1), "seeds": rows}
    (base_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    typer.echo("")
    for line in results_table(results, best):
        typer.echo(line)
    for line in table_note():
        typer.echo(line)
    for line in collapse_warnings(results):
        typer.echo(line)
    reason = "chosen on the validation mazes only"
    if best.scores is None:
        reason = "chosen on the last success rate (no validation mazes in this config)"
    typer.echo(f"\n{typer.style('best seed:', bold=True)} {best.seed} ({reason})")
    typer.echo(f"{typer.style('brain written:', bold=True)} {best_brain}")
    typer.echo(
        f"{typer.style('bundle written:', bold=True)} {best_bundle}  (load this one in the arena)"
    )
    typer.echo(f"⏱️  all seeds took {format_duration(seconds)}")
    typer.echo(f"\n✅ Done. Your brain: {best_brain}")


def _fixed_text(fixed: dict) -> str:
    """Example: "4 of 6 finished (easy-01 yes, easy-02 yes, medium-01 no, ...)"."""
    done = 0
    parts = []
    for level_id, finished in fixed.items():
        if finished:
            done += 1
            parts.append(f"{level_id} yes")
        else:
            parts.append(f"{level_id} no")
    return f"{done} of {len(fixed)} finished ({', '.join(parts)})"
