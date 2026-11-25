"""`minotaurus keygen`: make the key that signs your brain bundles."""

from pathlib import Path
from typing import Annotated

import typer


def run(
    out: Annotated[
        Path | None,
        typer.Option(
            help="Where to write the key. Default: $MINOTAURUS_SIGNING_KEY or ~/.config/minotaurus/signing.key"
        ),
    ] = None,
) -> None:
    from minotaurus.signing import SignatureError, default_key_path, generate_key

    path = out if out is not None else default_key_path()
    try:
        author = generate_key(path)
    except SignatureError as exc:
        typer.echo(f"minotaurus: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"key written: {path}")
    typer.echo(f"your author id: {author}")
    typer.echo("Keep the key file private and back it up: anyone who has it can sign as you.")
    typer.echo("Training signs its bundles with this key from now on.")
