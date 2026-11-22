"""`minotaurus play`: watch a dot move in the terminal (a brain, or random moves)."""

import argparse
import random
import sys
import time


def add_parser(commands) -> None:
    parser = commands.add_parser("play", help="watch a dot move in the terminal")
    parser.add_argument("--brain", default=None, help=".onnx brain to run (default: random moves)")
    parser.add_argument("--level", default="easy-01", help="level id (default easy-01)")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.1, help="seconds between steps")
    parser.add_argument(
        "--max-steps", type=int, default=None, help="stop early (default: step limit)"
    )
    parser.set_defaults(run=run)


def run(args: argparse.Namespace) -> None:
    from minotaurus.engine import LevelError, MazeEnv, load_level_by_id
    from minotaurus.engine.render import render_text

    try:
        level = load_level_by_id(args.level)
    except LevelError as exc:
        print(f"minotaurus: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    rng = random.Random(args.seed)
    brain = None
    if args.brain:
        from minotaurus.brain import BrainError, load_brain

        try:
            brain = load_brain(args.brain)
        except BrainError as exc:
            print(f"minotaurus: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
    env = MazeEnv(level)
    obs, _ = env.reset(seed=args.seed)
    limit = min(args.max_steps or env.step_limit, env.step_limit)
    tty = sys.stdout.isatty()
    outcome = "stopped"
    for step in range(1, limit + 1):
        action = brain(obs) if brain else rng.randrange(4)
        obs, _, done, truncated, _ = env.step(action)
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
    if brain and outcome != "reached the exit":
        raise SystemExit(1)
