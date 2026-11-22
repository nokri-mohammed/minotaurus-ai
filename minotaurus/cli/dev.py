"""`minotaurus dev`: start the server and the web page together."""

import argparse
import sys
from pathlib import Path


def add_parser(commands) -> None:
    parser = commands.add_parser("dev", help="start the server and the web page together")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--mock", action="store_true", help="page with a scripted run (no arena server yet)"
    )
    parser.set_defaults(run=run)


def dev_commands(port: int, mock: bool = False) -> list[tuple[list[str], str | None]]:
    """The processes of `dev`: (command, working directory). Both listen on 127.0.0.1 only."""
    web_dir = str(Path(__file__).resolve().parents[2] / "web")
    if mock:  # the fake arena lives inside Vite, so no Python server
        return [(["bun", "run", "dev:mock"], web_dir)]
    return [
        ([sys.executable, "-m", "minotaurus.cli", "serve", "--port", str(port)], None),
        (["bun", "run", "dev"], web_dir),
    ]


def run(args: argparse.Namespace) -> None:
    import shutil
    import subprocess

    if shutil.which("bun") is None:
        print("minotaurus: bun is not installed (needed for the web page)", file=sys.stderr)
        raise SystemExit(2)
    procs = [subprocess.Popen(cmd, cwd=cwd) for cmd, cwd in dev_commands(args.port, args.mock)]
    if not args.mock:
        print(f"\nServer: http://127.0.0.1:{args.port}/api/hello")
    print("Page:   http://127.0.0.1:5173   (Ctrl-C stops both)")
    try:
        procs[-1].wait()
    except KeyboardInterrupt:
        pass
    finally:
        for proc in procs:
            proc.terminate()
