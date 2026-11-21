"""observe(): the brain's input. obs_version 1 is the contract between training and racing."""

from __future__ import annotations

import numpy as np

from minotaurus.engine.levels import Level

OBS_VERSION = 1
DEFAULT_WINDOW = 5


def obs_size(window: int = DEFAULT_WINDOW) -> int:
    return 3 * window * window + 2


def observe(
    level: Level,
    pos: tuple[int, int],
    visited: set[tuple[int, int]] | frozenset[tuple[int, int]],
    window: int = DEFAULT_WINDOW,
) -> np.ndarray:
    """Window x window view centred on `pos`: walls, exit, visited layers, then exit direction.

    Layout (row-major, y down): walls, exit, visited, then [dx, dy] each in -1, 0 or 1
    (dx: -1 exit is left, 1 right; dy: -1 exit is up, 1 down). Outside the maze counts as wall.
    """
    half = window // 2
    n = window * window
    out = np.zeros(obs_size(window), dtype=np.float32)
    ex, ey = level.exit
    for row in range(window):
        for col in range(window):
            x, y = pos[0] - half + col, pos[1] - half + row
            i = row * window + col
            if level.is_wall(x, y):
                out[i] = 1.0
            if (x, y) == (ex, ey):
                out[n + i] = 1.0
            if (x, y) in visited:
                out[2 * n + i] = 1.0
    out[3 * n] = np.sign(ex - pos[0])
    out[3 * n + 1] = np.sign(ey - pos[1])
    return out
