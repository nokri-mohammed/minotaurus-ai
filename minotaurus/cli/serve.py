"""`minotaurus serve`: start the game server on 127.0.0.1."""

import argparse


def add_parser(commands) -> None:
    parser = commands.add_parser("serve", help="start the game server")
    parser.add_argument("--port", type=int, default=8000)
    parser.set_defaults(run=run)


def run(args: argparse.Namespace) -> None:
    import uvicorn

    uvicorn.run("minotaurus.server.app:app", host="127.0.0.1", port=args.port)
