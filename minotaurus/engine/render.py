"""Plain-text drawing of a maze with a dot, for the terminal."""

from __future__ import annotations

from minotaurus.engine.levels import Level


def render_text(level: Level, pos: tuple[int, int], visited: set[tuple[int, int]]) -> str:
    """# wall, @ the dot, o visited, E exit, . floor."""
    rows = []
    for y, row in enumerate(level.grid):
        chars = []
        for x, ch in enumerate(row):
            if (x, y) == pos:
                chars.append("@")
            elif ch == "E":
                chars.append("E")
            elif ch == "#":
                chars.append("#")
            elif (x, y) in visited:
                chars.append("o")
            else:
                chars.append(".")
        rows.append("".join(chars))
    return "\n".join(rows)
