"""Levels: load, validate and measure a maze. The only place that knows the level format."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "data" / "schemas"
LEVEL_DIR = ROOT / "data" / "levels"

DEFAULT_STEP_LIMIT_FACTOR = 4.0
# (dx, dy) per action: up, down, left, right. y grows downwards.
MOVES = ((0, -1), (0, 1), (-1, 0), (1, 0))


class LevelError(ValueError):
    """A level file is wrong. The message names the problem."""


@dataclass(frozen=True)
class Level:
    id: str
    name: str
    difficulty: str
    grid: tuple[str, ...]
    step_limit_factor: float = DEFAULT_STEP_LIMIT_FACTOR

    @property
    def width(self) -> int:
        return len(self.grid[0])

    @property
    def height(self) -> int:
        return len(self.grid)

    def _find(self, char: str) -> tuple[int, int]:
        for y, row in enumerate(self.grid):
            x = row.find(char)
            if x >= 0:
                return (x, y)
        raise LevelError(f"level {self.id!r} has no {char!r}")

    @property
    def start(self) -> tuple[int, int]:
        return self._find("S")

    @property
    def exit(self) -> tuple[int, int]:
        return self._find("E")

    def is_wall(self, x: int, y: int) -> bool:
        """Squares outside the maze count as walls."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return True
        return self.grid[y][x] == "#"

    @property
    def step_limit(self) -> int:
        return max(1, round(self.step_limit_factor * shortest_path_length(self)))


def _validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(json.loads((SCHEMA_DIR / name).read_text()))


def parse_level(data: dict) -> Level:
    errors = sorted(_validator("level.schema.json").iter_errors(data), key=lambda e: list(e.path))
    if errors:
        e = errors[0]
        where = ".".join(str(p) for p in e.path)
        if e.validator == "required":
            where = e.message  # "'name' is a required property"
        raise LevelError(
            f"bad level ({where}): {e.message}" if e.path else f"bad level: {e.message}"
        )
    grid = tuple(data["grid"])
    if len({len(r) for r in grid}) != 1:
        raise LevelError(f"level {data['id']!r}: grid rows must all have the same length")
    text = "".join(grid)
    if text.count("S") != 1:
        raise LevelError(f"level {data['id']!r}: grid needs exactly one S")
    if text.count("E") != 1:
        raise LevelError(f"level {data['id']!r}: grid needs exactly one E")
    level = Level(
        id=data["id"],
        name=data["name"],
        difficulty=data["difficulty"],
        grid=grid,
        step_limit_factor=float(data.get("step_limit_factor", DEFAULT_STEP_LIMIT_FACTOR)),
    )
    if _bfs(level) is None:
        raise LevelError(f"level {level.id!r}: the exit cannot be reached from the start")
    return level


def load_level(path: str | Path) -> Level:
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise LevelError(f"cannot read level {path}: {exc}") from exc
    return parse_level(data)


def load_level_by_id(level_id: str, level_dir: Path = LEVEL_DIR) -> Level:
    for path in sorted(level_dir.glob("*.json")):
        level = load_level(path)
        if level.id == level_id:
            return level
    raise LevelError(f"no level with id {level_id!r} in {level_dir}")


def load_all_levels(level_dir: Path = LEVEL_DIR) -> list[Level]:
    """Every *.json directly inside level_dir, loaded and validated, sorted by file name."""
    return [load_level(path) for path in sorted(level_dir.glob("*.json"))]


def select_by_difficulty(levels: list[Level], difficulty: str) -> tuple[Level, ...]:
    """The levels of one difficulty. Raises LevelError when there is none."""
    chosen = tuple(level for level in levels if level.difficulty == difficulty)
    if not chosen:
        raise LevelError(f"no level with difficulty {difficulty!r}")
    return chosen


def select_by_ids(levels: list[Level], ids: list[str]) -> tuple[Level, ...]:
    """The levels with these ids, in the order asked. Raises LevelError for an unknown id."""
    by_id = {level.id: level for level in levels}
    for level_id in ids:
        if level_id not in by_id:
            raise LevelError(f"no level with id {level_id!r}")
    return tuple(by_id[level_id] for level_id in ids)


def _bfs(level: Level) -> list[int] | None:
    """Shortest list of actions from start to exit, or None."""
    start, goal = level.start, level.exit
    came: dict[tuple[int, int], tuple[tuple[int, int], int] | None] = {start: None}
    queue = deque([start])
    while queue:
        pos = queue.popleft()
        if pos == goal:
            actions: list[int] = []
            while came[pos] is not None:
                pos, action = came[pos]  # type: ignore[misc]
                actions.append(action)
            return actions[::-1]
        for action, (dx, dy) in enumerate(MOVES):
            nxt = (pos[0] + dx, pos[1] + dy)
            if nxt not in came and not level.is_wall(*nxt):
                came[nxt] = (pos, action)
                queue.append(nxt)
    return None


def shortest_path_length(level: Level) -> int:
    path = _bfs(level)
    if path is None:
        raise LevelError(f"level {level.id!r}: the exit cannot be reached from the start")
    return len(path)


def shortest_path_actions(level: Level) -> list[int]:
    path = _bfs(level)
    if path is None:
        raise LevelError(f"level {level.id!r}: the exit cannot be reached from the start")
    return path
