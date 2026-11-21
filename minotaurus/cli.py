"""Command line: `minotaurus hello | train | serve`. Skeleton."""

import argparse

from minotaurus import __version__, engine, trainer


def main() -> None:
    parser = argparse.ArgumentParser(prog="minotaurus", description="minotaurus-ai " + __version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("hello", help="check the install")
    train = commands.add_parser("train", help="train a brain (not built yet)")
    train.add_argument("--config", required=True, help="path to a brain config .json")
    serve = commands.add_parser("serve", help="start the game server")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.command == "hello":
        print(f"Hello from minotaurus {__version__}: {engine.hello()}, {trainer.hello()}")
    elif args.command == "train":
        print(f"Training is not built yet. Config: {args.config}")
    elif args.command == "serve":
        import uvicorn

        uvicorn.run("minotaurus.server.app:app", host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
