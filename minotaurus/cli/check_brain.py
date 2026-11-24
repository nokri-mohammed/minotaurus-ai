"""`minotaurus check-brain <file>`."""

from typing import Annotated

import typer


def run(file: Annotated[str, typer.Argument(help="Path to the .onnx file.")]) -> None:
    import warnings

    from minotaurus.brain import BrainError, BrainWarning, load_brain

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", BrainWarning)
            brain = load_brain(file)
    except BrainError as exc:
        typer.echo(f"REJECTED: {exc}")
        raise typer.Exit(1) from exc
    for warning in caught:
        if issubclass(warning.category, BrainWarning):
            typer.echo(f"WARNING: {warning.message}")
    typer.echo(f"OK: {brain.name or '(no name)'} ({brain.method or 'unknown method'})")
