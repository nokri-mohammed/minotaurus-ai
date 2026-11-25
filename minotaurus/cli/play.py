"""`minotaurus play`."""

import random
import sys
import time
from typing import Annotated

import typer


def run(
    brain: Annotated[
        str | None, typer.Option(help=".onnx brain to run (default: random moves).")
    ] = None,
    level: Annotated[str, typer.Option(help="Level id.")] = "easy-01",
    seed: Annotated[int | None, typer.Option()] = None,
    delay: Annotated[float, typer.Option(help="Seconds between steps.")] = 0.1,
    max_steps: Annotated[int | None, typer.Option(help="Stop early (default: step limit).")] = None,
) -> None:
    from minotaurus.engine import LevelError, MazeEnv, load_level_by_id
    from minotaurus.engine.render import render_text

    try:
        level_data = load_level_by_id(level)
    except LevelError as exc:
        typer.echo(f"minotaurus: {exc}", err=True)
        raise typer.Exit(2) from exc
    rng = random.Random(seed)
    loaded = None
    if brain:
        from minotaurus.brain import BrainError, load_brain, player

        try:
            loaded = load_brain(brain)
        except BrainError as exc:
            typer.echo(f"minotaurus: {exc}", err=True)
            raise typer.Exit(2) from exc
        # as the arena plays it: the brain's own random-move rate and wall mask, seeded the same
        loaded = player(loaded, seed=f"{loaded.digest}|{level_data.id}")
    from minotaurus.brain import obs_version_of

    env = MazeEnv(level_data, obs_version=obs_version_of(loaded) if loaded else 1)
    obs, _ = env.reset(seed=seed)
    limit = min(max_steps or env.step_limit, env.step_limit)
    tty = sys.stdout.isatty()
    outcome = "stopped"
    for step in range(1, limit + 1):
        action = loaded(obs) if loaded else rng.randrange(4)
        obs, _, done, truncated, _ = env.step(action)
        if tty:
            typer.echo("\033[H\033[J", nl=False)
        typer.echo(render_text(level_data, env.pos, env.visited))
        typer.echo(f"{level_data.id}  step {step}/{env.step_limit}")
        if done:
            outcome = "reached the exit"
            break
        if truncated:
            outcome = "step limit reached"
            break
        time.sleep(delay)
    typer.echo(outcome)
    if loaded and outcome != "reached the exit":
        raise typer.Exit(1)
