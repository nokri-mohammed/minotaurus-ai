"""`minotaurus train --config <file>`."""

from pathlib import Path
from typing import Annotated

import typer


def run(
    config: Annotated[
        Path, typer.Option(help="Path to a brain config .json.", exists=True, dir_okay=False)
    ],
    runs_dir: Annotated[str, typer.Option(help="Where runs are written.")] = "runs",
    log_every: Annotated[int, typer.Option(help="Episodes per metrics line.")] = 10,
) -> None:
    from pydantic import ValidationError

    from minotaurus.engine.levels import LevelError
    from minotaurus.trainer.config import ConfigFile
    from minotaurus.trainer.train import train

    try:
        # Read the JSON file and build a checked ConfigFile; a wrong setting raises an error
        # that names it. `loaded` is the parsed object: loaded.name, loaded.episodes, ...
        loaded = ConfigFile.model_validate_json(config.read_text())
        # Only a check: the level ids exist on disk (the settings check cannot know that).
        loaded.resolve_levels()
    except (ValidationError, LevelError) as exc:
        typer.echo(f"minotaurus: bad config:\n{exc}", err=True)
        raise typer.Exit(2) from exc

    def show(line: dict) -> None:
        typer.echo(
            f"episode {line['episode']}/{loaded.episodes}  reward {line['avg_reward']:.3f}  "
            f"steps {line['avg_steps']:.1f}  success {line['success_rate']:.0%}  "
            f"epsilon {line['epsilon']:.3f}"
        )

    run_dir = train(loaded, runs_dir, log_every=log_every, progress=show)
    typer.echo(f"brain written: {run_dir / 'brain.onnx'}")
