"""Command line. One file per command; each has `add_parser(commands)` and a `run(args)`."""

import argparse

from minotaurus import __version__
from minotaurus.cli import check_brain, dev, hello, play, serve, train
from minotaurus.cli.dev import dev_commands

__all__ = ["dev_commands", "main"]

COMMANDS = [hello, train, check_brain, play, serve, dev]


def main() -> None:
    parser = argparse.ArgumentParser(prog="minotaurus", description="minotaurus-ai " + __version__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in COMMANDS:
        command.add_parser(commands)
    args = parser.parse_args()
    args.run(args)
