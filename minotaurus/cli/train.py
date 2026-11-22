"""`minotaurus train --config <file>`."""

from typing import Annotated

import typer


def run(
    config: Annotated[str, typer.Option(help="Path to a brain config .json.")],
    runs_dir: Annotated[str, typer.Option(help="Where runs are written.")] = "runs",
    log_every: Annotated[int, typer.Option(help="Episodes per metrics line.")] = 10,
) -> None:
    from minotaurus.trainer.config import ConfigError, load_config
    from minotaurus.trainer.train import train

    try:
        loaded = load_config(config)
    except ConfigError as exc:
        typer.echo(f"minotaurus: bad config: {exc}", err=True)
        raise typer.Exit(2) from exc

    def show(line: dict) -> None:
        typer.echo(
            f"episode {line['episode']}/{loaded.episodes}  reward {line['avg_reward']:.3f}  "
            f"steps {line['avg_steps']:.1f}  success {line['success_rate']:.0%}  "
            f"epsilon {line['epsilon']:.3f}"
        )

    run_dir = train(loaded, runs_dir, log_every=log_every, progress=show)
    typer.echo(f"brain written: {run_dir / 'brain.onnx'}")
