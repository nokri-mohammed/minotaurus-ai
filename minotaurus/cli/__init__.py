"""Command line (Typer). One file per command; each file has one function, `run`."""

import typer

from minotaurus.cli import check_brain, dev, hello, pack, play, serve, train
from minotaurus.cli.dev import dev_commands

__all__ = ["app", "dev_commands", "main"]

app = typer.Typer(
    help="minotaurus-ai: train a maze brain, run it, race it.",
    no_args_is_help=True,
    add_completion=False,
)
app.command("hello", help="Check the install.")(hello.run)
app.command("train", help="Train a brain and write brain.onnx.")(train.run)
app.command("check-brain", help="Check that a .onnx brain file is acceptable.")(check_brain.run)
app.command("pack", help="Pack a finished run into a .tar bundle to load in the arena.")(pack.run)
app.command("play", help="Watch a dot move in the terminal (a brain, or random moves).")(play.run)
app.command("serve", help="Start the game server on 127.0.0.1.")(serve.run)
app.command("dev", help="Start the server and the web page together.")(dev.run)


def main() -> None:
    app()
