"""`minotaurus hello`: check the install."""

import argparse

from minotaurus import __version__, engine, trainer


def add_parser(commands) -> None:
    commands.add_parser("hello", help="check the install").set_defaults(run=run)


def run(args: argparse.Namespace) -> None:
    print(f"Hello from minotaurus {__version__}: {engine.hello()}, {trainer.hello()}")
