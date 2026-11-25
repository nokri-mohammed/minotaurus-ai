"""`minotaurus dev`."""

import sys
from pathlib import Path
from typing import Annotated

import typer


def dev_commands(port: int) -> list[tuple[list[str], str | None]]:
    """The processes of `dev`: (command, working directory). Both listen on 127.0.0.1 only."""
    web_dir = str(Path(__file__).resolve().parents[2] / "web")
    return [
        ([sys.executable, "-m", "minotaurus.cli", "serve", "--port", str(port)], None),
        (["bun", "run", "dev"], web_dir),
    ]


def run(
    port: Annotated[int, typer.Option(help="Port of the Python server.")] = 8000,
) -> None:
    import shutil
    import subprocess

    if shutil.which("bun") is None:
        typer.echo("minotaurus: bun is not installed (needed for the web page)", err=True)
        raise typer.Exit(2)
    procs = [subprocess.Popen(cmd, cwd=cwd) for cmd, cwd in dev_commands(port)]
    typer.echo(f"\nServer: http://127.0.0.1:{port}/api/hello")
    typer.echo("Page:   http://127.0.0.1:5173   (Ctrl-C stops both)")
    try:
        procs[-1].wait()
    except KeyboardInterrupt:
        pass
    finally:
        for proc in procs:
            proc.terminate()
