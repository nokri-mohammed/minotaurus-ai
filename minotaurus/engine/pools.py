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


def walls(level: Level) -> tuple[str, ...]:
    """The grid with S and E turned back into floor: what is wall and what is not."""
    rows = []
    for row in level.grid:
        rows.append(row.replace("S", ".").replace("E", "."))
    return tuple(rows)


def _draw(
    first_seed: int, count: int, size: int, taken: set[tuple[str, ...]], random_start: bool
) -> tuple[Level, ...]:
    """`count` mazes with new layouts. Every layout used is added to `taken`.

    A layout is the walls only, so with random_start the same walls with another start square
    still count as a maze already used.
    """
    chosen = []
    seed = first_seed
    tries_left = count * MAX_TRIES_PER_MAZE + 50
    while len(chosen) < count:
        if tries_left == 0:
            raise LevelError(f"cannot make {count} different mazes of size {size}: too few exist")
        tries_left -= 1
        level = generate_maze(seed, size, random_start)
        seed += 1
        layout = walls(level)
        if layout in taken:
            continue  # same layout as one already used: skip it
        taken.add(layout)
        chosen.append(level)
    return tuple(chosen)


def practice_mazes(size: int, first_seed: int, count: int) -> tuple[Level, ...]:
    """Up to `count` mazes with different walls, for a curriculum stage (training only).

    Small sizes have few mazes (5 x 5 has 2, 7 x 7 has 14), so this returns as many as it finds
    instead of refusing. A maze of one size can never be a maze of another size, so these never
    overlap the validation or test pools of a bigger size.
    """
    taken: set[tuple[str, ...]] = set()
    chosen = []
    seed = first_seed
    tries_left = count * MAX_TRIES_PER_MAZE + 50
    while len(chosen) < count and tries_left > 0:
        tries_left -= 1
        level = generate_maze(seed, size)
        seed += 1
        layout = walls(level)
        if layout not in taken:
            taken.add(layout)
            chosen.append(level)
    return tuple(chosen)


def build_pools(
    size: int,
    maze_seed: int,
    train: int,
    validation: int,
    test: int,
    random_start: bool = False,
) -> Pools:
    """Test first, then validation, then train: a train maze is never a test or validation maze.

    random_start=True gives every maze a start square picked by its seed (off by default).
    """
    taken: set[tuple[str, ...]] = set()
    test_mazes = _draw(maze_seed + 2 * SEED_GAP, test, size, taken, random_start)
    validation_mazes = _draw(maze_seed + SEED_GAP, validation, size, taken, random_start)
    train_mazes = _draw(maze_seed, train, size, taken, random_start)
    return Pools(train=train_mazes, validation=validation_mazes, test=test_mazes)
