"""observe(): the brain's input. obs_version 1 is the contract between training and racing.

Since 2026-11-24 the visited layer is a visit count, min(visits, VISIT_CAP), as a raw number: a
square walked on once is 1.0 as before, so a brain trained on the old yes/no layer sees the same
input until a square is visited a second time. The repo owner chose to keep obs_version 1 for this
(a breaking change inside version 1); exported brains say so with the metadata visited="counts".
"""

from __future__ import annotations

from collections.abc import Mapping
from collections.abc import Set as AbstractSet

import numpy as np

from minotaurus.engine.levels import MOVES, Level

OBS_VERSION = 1
DEFAULT_WINDOW = 5
VISIT_CAP = 3  # the visited layer shows 0, 1, 2 or 3 (3 = three visits or more)
# .onnx metadata: which visited layer a brain was trained on. Brains exported since 2026-11-24
# say "counts"; a brain without the key was trained on the old yes/no layer.
VISITED_KEY = "visited"
VISITED_COUNTS = "counts"


def obs_size(window: int = DEFAULT_WINDOW) -> int:
    return 3 * window * window + 2


def obs_bounds(window: int = DEFAULT_WINDOW) -> tuple[np.ndarray, np.ndarray]:
    """Lowest and highest value of every input: walls and exit 0..1, visited 0..VISIT_CAP, the
    exit direction -1..1."""
    n = window * window
    low = np.zeros(obs_size(window), dtype=np.float32)
    high = np.ones(obs_size(window), dtype=np.float32)
    for i in range(2 * n, 3 * n):
        high[i] = float(VISIT_CAP)
    low[3 * n] = -1.0
    low[3 * n + 1] = -1.0
    return low, high


def visit_count(
    visits: Mapping[tuple[int, int], int] | AbstractSet[tuple[int, int]], square
) -> int:
    """How often the dot was on `square`. A set means every square in it was visited once."""
    if isinstance(visits, Mapping):
        return visits.get(square, 0)
    if square in visits:
        return 1
    return 0


def observe(
    level: Level,
    pos: tuple[int, int],
    visits: Mapping[tuple[int, int], int] | AbstractSet[tuple[int, int]],
    window: int = DEFAULT_WINDOW,
) -> np.ndarray:
    """Window x window view centred on `pos`: walls, exit, visited layers, then exit direction.

    Layout (row-major, y down): walls, exit, visited, then [dx, dy] each in -1, 0 or 1
    (dx: -1 exit is left, 1 right; dy: -1 exit is up, 1 down). Outside the maze counts as wall.
    `visits` maps a square to its visit count; the visited layer shows min(count, VISIT_CAP).
    A set of squares still works and means each was visited once (the old yes/no layer).
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
            count = visit_count(visits, (x, y))
            count = min(count, VISIT_CAP)
            out[2 * n + i] = float(count)
    out[3 * n] = np.sign(ex - pos[0])
    out[3 * n + 1] = np.sign(ey - pos[1])
    return out


def blocked_moves(obs: np.ndarray, window: int = DEFAULT_WINDOW) -> list[bool]:
    """For each move (up, down, left, right): True when the square next to the dot in that
    direction is a wall the dot can see (the walls layer of `obs`).

    Example: at the start of easy-01 (wall above and to the left) -> [True, False, True, False].
    """
    half = window // 2
    blocked = []
    for dx, dy in MOVES:
        index = (half + dy) * window + (half + dx)
        blocked.append(bool(obs[index] == 1.0))
    return blocked


def free_moves(obs: np.ndarray, window: int = DEFAULT_WINDOW) -> list[int]:
    """The moves that do not walk into a visible wall, in move order (up, down, left, right)."""
    free = []
    for action, blocked in enumerate(blocked_moves(obs, window)):
        if not blocked:
            free.append(action)
    return free
