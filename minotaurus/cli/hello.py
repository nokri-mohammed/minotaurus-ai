"""`minotaurus hello`."""

import typer

from minotaurus import __version__, engine, trainer


def run() -> None:
    typer.echo(f"Hello from minotaurus {__version__}: {engine.hello()}, {trainer.hello()}")
