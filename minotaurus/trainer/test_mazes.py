"""Save a few mazes from the real test pile as level files, so the portal can show them.

Run: uv run python -m minotaurus.trainer.test_mazes
The pile comes from data/examples/dqn-mixed-brain.json. Change that config's maze settings and
run this again (a test fails until you do).
"""

from __future__ import annotations

import json
from pathlib import Path

from minotaurus.engine.levels import LEVEL_DIR, ROOT, TEST_MAZE_DIR, Level
from minotaurus.engine.pools import Pools
from minotaurus.trainer.config import ConfigFile

EXAMPLE_CONFIG = ROOT / "data" / "examples" / "dqn-mixed-brain.json"
PER_SIZE = 4


def pick_test_mazes(pools: Pools, per_size: int = PER_SIZE) -> list[Level]:
    """The first `per_size` test mazes of each size, smallest size first, named test-09-01 ...

    Example: sizes 9, 11, 13 with per_size 4 -> test-09-01 ... test-09-04, test-11-01 ... test-13-04.
    """
    by_size: dict[int, list[Level]] = {}
    for level in pools.test:
        if level.width not in by_size:
            by_size[level.width] = []
        if len(by_size[level.width]) < per_size:
            by_size[level.width].append(level)
    picked = []
    for size in sorted(by_size):
        for number, level in enumerate(by_size[size], start=1):
            picked.append(
                Level(
                    id=f"test-{size:02d}-{number:02d}",
                    name=f"Test maze {size}x{size} #{number}",
                    difficulty=level.difficulty,
                    grid=level.grid,
                )
            )
    return picked


def write_test_mazes(out_dir: Path = TEST_MAZE_DIR) -> list[Path]:
    """Write the picked mazes as level files. Old files in the folder are replaced."""
    config = ConfigFile.model_validate_json(EXAMPLE_CONFIG.read_text())
    pools = config.resolve_pools()
    if pools is None:
        raise ValueError("the example config has no generated mazes")
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.json"):
        old.unlink()
    written = []
    for level in pick_test_mazes(pools):
        data = {
            "id": level.id,
            "name": level.name,
            "difficulty": level.difficulty,
            "grid": list(level.grid),
        }
        path = out_dir / f"{level.id}.json"
        path.write_text(json.dumps(data, indent=2) + "\n")
        written.append(path)
    return written


if __name__ == "__main__":
    files = write_test_mazes()
    print(f"written: {len(files)} files in {LEVEL_DIR / 'test-mazes'}")
