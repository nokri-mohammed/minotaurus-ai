"""Make a maze from a seed. The same seed and size always give the same maze."""

from __future__ import annotations

import random
from collections import deque

from minotaurus.engine.levels import MOVES, Level, LevelError, parse_level

MIN_SIZE = 5
MAX_SIZE = 41


def _difficulty_for(size: int) -> str:
    if size <= 9:
        return "easy"
    if size <= 17:
        return "medium"
    return "hard"


def _carve(rng: random.Random, size: int) -> list[list[str]]:
    """Dig corridors with a depth-first walk. Cells sit on odd x and y; walls stay between them."""
    cells = [["#"] * size for _ in range(size)]
    start = (1, 1)
    cells[1][1] = "."
    stack = [start]
    while stack:
        x, y = stack[-1]
        options = []
        for dx, dy in MOVES:
            nx, ny = x + 2 * dx, y + 2 * dy
            if 1 <= nx < size - 1 and 1 <= ny < size - 1 and cells[ny][nx] == "#":
                options.append((dx, dy))
        if not options:
            stack.pop()
            continue
        dx, dy = rng.choice(options)
        cells[y + dy][x + dx] = "."  # knock down the wall between the two cells
        cells[y + 2 * dy][x + 2 * dx] = "."
        stack.append((x + 2 * dx, y + 2 * dy))
    return cells


def _farthest(cells: list[list[str]], start: tuple[int, int]) -> tuple[int, int]:
    """The floor square with the longest walk from start (the first one found on a tie)."""
    size = len(cells)
    distance = {start: 0}
    queue = deque([start])
    best = start
    while queue:
        x, y = queue.popleft()
        if distance[(x, y)] > distance[best]:
            best = (x, y)
        for dx, dy in MOVES:
            nxt = (x + dx, y + dy)
            inside = 0 <= nxt[0] < size and 0 <= nxt[1] < size
            if inside and cells[nxt[1]][nxt[0]] == "." and nxt not in distance:
                distance[nxt] = distance[(x, y)] + 1
                queue.append(nxt)
    return best


def _floor_squares(cells: list[list[str]]) -> list[tuple[int, int]]:
    """Every floor square, row by row from the top left."""
    squares = []
    for y, row in enumerate(cells):
        for x, cell in enumerate(row):
            if cell == ".":
                squares.append((x, y))
    return squares


def generate_maze(seed: int, size: int, random_start: bool = False) -> Level:
    """A square maze, size x size, exit at the far end of the longest walk from the start.

    The start is the top left square, or with random_start=True a floor square picked by the seed
    (the id then ends in "-r", so it never clashes with the top-left maze of the same seed).

    Example: generate_maze(7, 9) -> Level(id="gen-9-7", ...), the same one every time.
    """
    if size % 2 == 0 or size < MIN_SIZE or size > MAX_SIZE:
        raise LevelError(f"maze size must be odd, from {MIN_SIZE} to {MAX_SIZE}, not {size}")
    rng = random.Random(seed)
    cells = _carve(rng, size)
    start = (1, 1)
    level_id = f"gen-{size}-{seed}"
    if random_start:
        # drawn after carving, so the walls are the same as the top-left maze of this seed
        start = rng.choice(_floor_squares(cells))
        level_id += "-r"
    exit_x, exit_y = _farthest(cells, start)
    cells[start[1]][start[0]] = "S"
    cells[exit_y][exit_x] = "E"
    rows = []
    for row in cells:
        rows.append("".join(row))
    return parse_level(
        {
            "id": level_id,
            "name": f"Maze {seed}",
            "difficulty": _difficulty_for(size),
            "grid": rows,
        }
    )
