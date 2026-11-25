"""`minotaurus sign <bundle.tar>`: sign a bundle that already exists."""

from pathlib import Path
from typing import Annotated

import typer


def signed_name(bundle: Path) -> Path:
    """a.tar becomes a.signed.tar; a name that already ends in .signed.tar stays."""
    if bundle.name.endswith(".signed.tar"):
        return bundle
    return bundle.with_name(bundle.name.removesuffix(".tar") + ".signed.tar")


def run(
    bundle: Annotated[
        Path, typer.Argument(help="The .tar bundle to sign.", exists=True, dir_okay=False)
    ],
    key: Annotated[
        Path | None, typer.Option(help="The key file. Default: the key from keygen.")
    ] = None,
    out: Annotated[
        Path | None, typer.Option(help="Write to this file instead of in place.")
    ] = None,
) -> None:
    from minotaurus.bundle import BundleError, read_bundle, sign_bundle
    from minotaurus.signing import default_key_path

    key_path = key if key is not None else default_key_path()
    if out is None:
        out = signed_name(bundle)  # the unsigned file stays as it is
    try:
        path = sign_bundle(bundle, key_path, out)
        signer = read_bundle(path.read_bytes()).signer
    except BundleError as exc:
        typer.echo(f"minotaurus: cannot sign: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"signed: {path}")
    typer.echo(f"author id: {signer}")
