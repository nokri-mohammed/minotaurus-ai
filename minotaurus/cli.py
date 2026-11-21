"""Command line: `minotaurus hello | play | train | serve | dev`."""

import argparse
import random
import sys
import time
from pathlib import Path

from minotaurus import __version__, engine, trainer


def main() -> None:
    parser = argparse.ArgumentParser(prog="minotaurus", description="minotaurus-ai " + __version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("hello", help="check the install")
    train = commands.add_parser("train", help="train a brain (not built yet)")
    train.add_argument("--config", required=True, help="path to a brain config .json")
    play = commands.add_parser("play", help="watch a dot move in the terminal (random brain)")
    play.add_argument("--level", default="easy-01", help="level id (default easy-01)")
    play.add_argument("--seed", type=int, default=None)
    play.add_argument("--delay", type=float, default=0.1, help="seconds between steps")
    play.add_argument(
        "--max-steps", type=int, default=None, help="stop early (default: step limit)"
    )
    serve = commands.add_parser("serve", help="start the game server")
    serve.add_argument("--port", type=int, default=8000)
    dev = commands.add_parser("dev", help="start the server and the web page together")
    dev.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.command == "hello":
        print(f"Hello from minotaurus {__version__}: {engine.hello()}, {trainer.hello()}")
    elif args.command == "play":
        play_random(args)
    elif args.command == "train":
        print(f"Training is not built yet. Config: {args.config}")
    elif args.command == "dev":
        run_dev(args.port)
    elif args.command == "serve":
        import uvicorn

        uvicorn.run("minotaurus.server.app:app", host="127.0.0.1", port=args.port)


def play_random(args: argparse.Namespace) -> None:
    from minotaurus.engine import LevelError, MazeEnv, load_level_by_id
    from minotaurus.engine.render import render_text

    try:
        level = load_level_by_id(args.level)
    except LevelError as exc:
        print(f"minotaurus: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    rng = random.Random(args.seed)
    env = MazeEnv(level)
    env.reset(seed=args.seed)
    limit = min(args.max_steps or env.step_limit, env.step_limit)
    tty = sys.stdout.isatty()
    outcome = "stopped"
    for step in range(1, limit + 1):
        _, _, done, truncated, _ = env.step(rng.randrange(4))
        if tty:
            print("\033[H\033[J", end="")
        print(render_text(level, env.pos, env.visited))
        print(f"{level.id}  step {step}/{env.step_limit}")
        if done:
            outcome = "reached the exit"
            break
        if truncated:
            outcome = "step limit reached"
            break
        time.sleep(args.delay)
    print(outcome)


def dev_commands(port: int) -> list[tuple[list[str], str | None]]:
    """The two processes of `dev`: (command, working directory). Both listen on 127.0.0.1 only."""
    web_dir = str(Path(__file__).resolve().parents[1] / "web")
    return [
        ([sys.executable, "-m", "minotaurus.cli", "serve", "--port", str(port)], None),
        (["bun", "run", "dev"], web_dir),
    ]


def run_dev(port: int) -> None:
    import shutil
    import subprocess

    if shutil.which("bun") is None:
        print("minotaurus: bun is not installed (needed for the web page)", file=sys.stderr)
        raise SystemExit(2)
    procs = [subprocess.Popen(cmd, cwd=cwd) for cmd, cwd in dev_commands(port)]
    print(f"\nServer: http://127.0.0.1:{port}/api/hello")
    print("Page:   http://127.0.0.1:5173   (Ctrl-C stops both)")
    try:
        procs[0].wait()
    except KeyboardInterrupt:
        pass
    finally:
        for proc in procs:
            proc.terminate()


if __name__ == "__main__":
    main()
