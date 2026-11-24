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
    """The carved walls: the grid with S and E turned back into what they were when the maze was
    dug. S was floor; E was floor inside the maze, or wall when it is a gap in the outer wall
    (border_exit). So the same maze with another start or exit has the same walls."""
    last_row = len(level.grid) - 1
    rows = []
    for y, row in enumerate(level.grid):
        exit_was = "."
        x = row.find("E")
        if x >= 0 and (y in (0, last_row) or x in (0, len(row) - 1)):
            exit_was = "#"
        rows.append(row.replace("S", ".").replace("E", exit_was))
    return tuple(rows)


def _draw(
    first_seed: int,
    count: int,
    size: int,
    taken: set[tuple[str, ...]],
    random_start: bool,
    border_exit: bool = False,
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
        level = generate_maze(seed, size, random_start, border_exit)
        seed += 1
        layout = walls(level)
        if layout in taken:
            continue  # same layout as one already used: skip it
        taken.add(layout)
        chosen.append(level)
    return tuple(chosen)


def practice_mazes(
    size: int, first_seed: int, count: int, random_start: bool = False, border_exit: bool = False
) -> tuple[Level, ...]:
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
        level = generate_maze(seed, size, random_start, border_exit)
        seed += 1
        layout = walls(level)
        if layout not in taken:
            taken.add(layout)
            chosen.append(level)
    return tuple(chosen)


def _draw_mixed(
    first_seed: int,
    count: int,
    sizes: tuple[int, ...],
    taken: set[tuple[str, ...]],
    random_start: bool,
    border_exit: bool,
) -> tuple[Level, ...]:
    """`count` mazes split evenly over `sizes`, one size after the other in turn.

    Example: count 7 over sizes (9, 11, 13) -> 3 of size 9, 2 of size 11, 2 of size 13, in the
    order 9, 11, 13, 9, 11, 13, 9.
    """
    if count < len(sizes):
        raise LevelError(f"a pool of {count} mazes cannot hold {len(sizes)} sizes")
    each = count // len(sizes)
    extra = count % len(sizes)  # the first sizes get one more
    per_size = []
    for index, size in enumerate(sizes):
        wanted = each
        if index < extra:
            wanted += 1
        per_size.append(_draw(first_seed, wanted, size, taken, random_start, border_exit))
    mixed = []
    for turn in range(each + 1):
        for mazes in per_size:
            if turn < len(mazes):
                mixed.append(mazes[turn])
    return tuple(mixed)


def build_pools(
    size: int,
    maze_seed: int,
    train: int,
    validation: int,
    test: int,
    random_start: bool = False,
    border_exit: bool = False,
    sizes: tuple[int, ...] | None = None,
) -> Pools:
    """Test first, then validation, then train: a train maze is never a test or validation maze.

    random_start=True gives every maze a start square picked by its seed, border_exit=True puts
    its exit in the outer wall (both off by default). Neither changes the walls, so the pools hold
    the same mazes as without them.

    With `sizes` (for example (9, 11, 13)) every pool is split evenly over those sizes and the
    sizes alternate in the list, so the first mazes of a pool show every size. `size` is then
    ignored for drawing.
    """
    taken: set[tuple[str, ...]] = set()
    if sizes is not None:
        test_mazes = _draw_mixed(
            maze_seed + 2 * SEED_GAP, test, sizes, taken, random_start, border_exit
        )
        validation_mazes = _draw_mixed(
            maze_seed + SEED_GAP, validation, sizes, taken, random_start, border_exit
        )
        train_mazes = _draw_mixed(maze_seed, train, sizes, taken, random_start, border_exit)
        return Pools(train=train_mazes, validation=validation_mazes, test=test_mazes)
    test_mazes = _draw(maze_seed + 2 * SEED_GAP, test, size, taken, random_start, border_exit)
    validation_mazes = _draw(
        maze_seed + SEED_GAP, validation, size, taken, random_start, border_exit
    )
    train_mazes = _draw(maze_seed, train, size, taken, random_start, border_exit)
    return Pools(train=train_mazes, validation=validation_mazes, test=test_mazes)
