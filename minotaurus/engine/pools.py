"""Train, validation and test mazes. No maze layout is in two pools."""

from __future__ import annotations

from dataclasses import dataclass

from minotaurus.engine.generate import generate_maze
from minotaurus.engine.levels import Level, LevelError

# Each pool draws seeds from its own range, so the pools start apart.
SEED_GAP = 1_000_000
MAX_TRIES_PER_MAZE = 20


@dataclass(frozen=True)
class Pools:
    train: tuple[Level, ...]
    validation: tuple[Level, ...]
    test: tuple[Level, ...]


def _draw(first_seed: int, count: int, size: int, taken: set[tuple[str, ...]]) -> tuple[Level, ...]:
    """`count` mazes with new layouts. Every layout used is added to `taken`."""
    chosen = []
    seed = first_seed
    tries_left = count * MAX_TRIES_PER_MAZE + 50
    while len(chosen) < count:
        if tries_left == 0:
            raise LevelError(f"cannot make {count} different mazes of size {size}: too few exist")
        tries_left -= 1
        level = generate_maze(seed, size)
        seed += 1
        if level.grid in taken:
            continue  # same layout as one already used: skip it
        taken.add(level.grid)
        chosen.append(level)
    return tuple(chosen)


def build_pools(size: int, maze_seed: int, train: int, validation: int, test: int) -> Pools:
    """Test first, then validation, then train: a train maze is never a test or validation maze."""
    taken: set[tuple[str, ...]] = set()
    test_mazes = _draw(maze_seed + 2 * SEED_GAP, test, size, taken)
    validation_mazes = _draw(maze_seed + SEED_GAP, validation, size, taken)
    train_mazes = _draw(maze_seed, train, size, taken)
    return Pools(train=train_mazes, validation=validation_mazes, test=test_mazes)
