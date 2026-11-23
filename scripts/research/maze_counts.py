"""How many different mazes each size has, and how often a random walk finds the exit in time.

python scripts/research/maze_counts.py
"""

from __future__ import annotations

import random
import statistics


def main() -> None:
    from minotaurus.engine.env import move
    from minotaurus.engine.generate import generate_maze
    from minotaurus.engine.levels import shortest_path_length
    from minotaurus.engine.pools import build_pools, walls

    for size in (5, 7, 9):
        layouts = set()
        for seed in range(20_000):
            layouts.add(walls(generate_maze(seed, size)))
        print(f"size {size}: {len(layouts)} different mazes in 20 000 seeds")

    for size, validation in ((9, 50), (11, 100)):
        pools = build_pools(size, 1, 222, validation, validation)
        rng = random.Random(0)
        within = 0
        needed = []
        for level in pools.train[:100]:
            for _ in range(5):
                pos, steps = level.start, 0
                while pos != level.exit and steps < 200_000:
                    pos, _ = move(level, pos, rng.randrange(4))
                    steps += 1
                needed.append(steps / shortest_path_length(level))
                if steps <= level.step_limit:
                    within += 1
        print(
            f"size {size}: a random walk finds the exit within the step limit in "
            f"{within} of {len(needed)} tries; median {statistics.median(needed):.0f} x the "
            "shortest path"
        )


if __name__ == "__main__":
    main()
