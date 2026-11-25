"""`minotaurus pack <run folder>`: write the bundle of a finished run (for runs made before bundles)."""

from pathlib import Path
from typing import Annotated

import typer


def run(
    run_dir: Annotated[
        Path,
        typer.Argument(
            help="A run folder with brain.onnx and config.json.", exists=True, file_okay=False
        ),
    ],
    out: Annotated[Path | None, typer.Option(help="Where to write the .tar.")] = None,
) -> None:
    from minotaurus.brain import BrainError
    from minotaurus.bundle import BundleError, build_bundle, read_bundle
    from minotaurus.signing import existing_default_key

    try:
        path = build_bundle(run_dir, out, signing_key=existing_default_key())
        signer = read_bundle(path.read_bytes()).signer  # the same check the server makes
    except (BundleError, BrainError) as exc:
        typer.echo(f"minotaurus: cannot pack: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"bundle written: {path}")
    if signer is not None:
        typer.echo(f"signed, author id {signer}")
