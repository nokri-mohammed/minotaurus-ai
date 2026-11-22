"""`minotaurus check-brain <file>`: check that a .onnx brain file is acceptable."""

import argparse


def add_parser(commands) -> None:
    parser = commands.add_parser("check-brain", help="check that a .onnx brain file is acceptable")
    parser.add_argument("file", help="path to the .onnx file")
    parser.set_defaults(run=run)


def run(args: argparse.Namespace) -> None:
    from minotaurus.brain import BrainError, load_brain

    try:
        brain = load_brain(args.file)
    except BrainError as exc:
        print(f"REJECTED: {exc}")
        raise SystemExit(1) from exc
    print(f"OK: {brain.name or '(no name)'} ({brain.method or 'unknown method'})")
