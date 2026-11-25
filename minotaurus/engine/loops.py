"""Loop watch: has the dot been in the same state before?

A state is the dot's square and exactly what the brain sees there. A brain plays the same move in
the same state, so a state seen for the third time means the dot is going round in circles: the
visit counts in the input stop changing once they reach their cap.
"""

from __future__ import annotations

import numpy as np

from minotaurus.engine.levels import MOVES

LOOP_REPEATS = 3  # the same state this many times in one run counts as a loop


class LoopWatch:
    """Counts how often each state came up in one run."""

    def __init__(self) -> None:
        self.counts: dict[tuple, int] = {}

    def see(self, pos: tuple[int, int], obs: np.ndarray) -> int:
        """Note the state and return how many times it has now come up (1 the first time)."""
        key = (pos, np.asarray(obs, dtype=np.float32).tobytes())
        count = self.counts.get(key, 0) + 1
        self.counts[key] = count
        return count


class DeadReckoning:
    """Follows the dot's square from the moves alone, for code that never sees the square.

    The start is (0, 0). A move changes the square unless the wall layer of the input it was
    made from shows a wall that way (then it was a bump). Only differences matter, so this is as
    good as the real square for telling states apart.
    """

    def __init__(self, blocked_moves) -> None:
        self.pos = (0, 0)
        self._blocked = blocked_moves  # obs -> [up, down, left, right] wall flags
        self._last: tuple[np.ndarray, int] | None = None

    def update(self, obs: np.ndarray) -> tuple[int, int]:
        """The square for the observation just received, after the previous move."""
        if self._last is not None:
            before, action = self._last
            if not self._blocked(before)[action]:
                dx, dy = MOVES[action]
                self.pos = (self.pos[0] + dx, self.pos[1] + dy)
        return self.pos

    def moved(self, obs: np.ndarray, action: int) -> None:
        self._last = (obs, action)
