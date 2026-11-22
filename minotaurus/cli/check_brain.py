"""`minotaurus check-brain <file>`."""

from typing import Annotated

import typer


def run(file: Annotated[str, typer.Argument(help="Path to the .onnx file.")]) -> None:
    from minotaurus.brain import BrainError, load_brain

    try:
        brain = load_brain(file)
    except BrainError as exc:
        typer.echo(f"REJECTED: {exc}")
        raise typer.Exit(1) from exc
    typer.echo(f"OK: {brain.name or '(no name)'} ({brain.method or 'unknown method'})")
