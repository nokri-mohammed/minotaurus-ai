"""`minotaurus train --config <file>`."""

import json
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
) -> None:
    from pydantic import ValidationError

    from minotaurus.engine.levels import LevelError
    from minotaurus.trainer.config import ConfigFile
    from minotaurus.trainer.plot import plot_metrics, read_metrics
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

    def show(line: dict) -> None:
        typer.echo(
            f"episode {line['episode']}/{loaded.episodes}  reward {line['avg_reward']:.3f}  "
            f"steps {line['avg_steps']:.1f}  success {line['success_rate']:.0%}  "
            f"epsilon {line['epsilon']:.3f}"
        )

    started = time.monotonic()
    run_dir = train(
        loaded, levels, runs_dir, log_every=log_every, progress=show, pools=pools, stages=stages
    )
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
    if plot:
        graph = plot_metrics(run_dir / "metrics.jsonl", run_dir / "training.png", title=loaded.name)
        typer.echo(f"{typer.style('graph written:', bold=True)} {graph}")
    for text in summarize_run(run_dir, seconds):
        typer.echo(text)
    typer.echo(f"\n✅ Done. Your brain: {run_dir / 'brain.onnx'}")
