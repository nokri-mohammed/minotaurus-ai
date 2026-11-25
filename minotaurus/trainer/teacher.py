"""The teacher for imitation: from any square, the move that goes nearest the exit.

It knows the whole maze, which the brain does not (the brain sees a 5 x 5 window). Training only.
"""

from __future__ import annotations

from minotaurus.engine.levels import MOVES, Level
from minotaurus.trainer.shaping import distances


class Teacher:
    def __init__(self, level: Level) -> None:
        self.level = level
        self.distance = distances(level)

    def move(self, pos: tuple[int, int]) -> int:
        """The move (0 up, 1 down, 2 left, 3 right) to the neighbour with the fewest steps left.

        A tie goes to the first move in order. At the exit, or on a square that cannot reach it,
        any move is as good: it returns 0.
        """
        best_action = 0
        best_steps = None
        for action, (dx, dy) in enumerate(MOVES):
            nxt = (pos[0] + dx, pos[1] + dy)
            steps = self.distance.get(nxt)
            if steps is None:
                continue
            if best_steps is None or steps < best_steps:
                best_action = action
                best_steps = steps
        return best_action
