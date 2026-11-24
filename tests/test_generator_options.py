"""Generator options in the config (2026-11-24): border_exit (new) and random_start."""

import json

import pytest
from pydantic import ValidationError

from minotaurus.engine.generate import generate_maze
from minotaurus.engine.levels import MOVES, shortest_path_length
from minotaurus.engine.pools import build_pools, walls
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.shaping import potential
from minotaurus.trainer.train import train
from tests.test_trainer import small_dqn_config


def on_border(level) -> bool:
    x, y = level.exit
    last = level.width - 1
    return x in (0, last) or y in (0, last)


def is_corner(level) -> bool:
    x, y = level.exit
    last = level.width - 1
    return x in (0, last) and y in (0, last)


def generated(**options) -> dict:
    data = small_dqn_config(3)
    settings = {"size": 9, "maze_seed": 1, "train": 6, "validation": 3, "test": 3}
    settings.update(options)
    data["levels"] = {"generated": settings}
    return data


# ---- generator ----


@pytest.mark.parametrize("seed", [1, 2, 3, 17, 40])
@pytest.mark.parametrize("size", [5, 9, 15])
def test_border_exit_is_a_gap_in_the_outer_wall(seed, size):
    level = generate_maze(seed, size, border_exit=True)
    assert on_border(level) and not is_corner(level)
    assert level.id.endswith("-b")
    assert shortest_path_length(level) >= 1  # solvable
    x, y = level.exit
    floor_next = 0
    for dx, dy in MOVES:
        if not level.is_wall(x + dx, y + dy):
            floor_next += 1
    assert floor_next == 1  # a gap with one floor square behind it


@pytest.mark.parametrize("seed", [1, 5, 9])
def test_border_exit_keeps_the_walls_and_is_the_farthest_gap(seed):
    plain = generate_maze(seed, 11)
    level = generate_maze(seed, 11, border_exit=True)
    assert walls(level) == walls(plain)  # the same carved maze, only the exit moved
    best = shortest_path_length(level)
    for y in range(level.height):
        for x in range(level.width):
            if not (x in (0, level.width - 1) or y in (0, level.height - 1)):
                continue
            grid = [list(row.replace("E", "#")) for row in level.grid]
            inner = 0
            for dx, dy in MOVES:
                nx, ny = x + dx, y + dy
                if 0 <= nx < level.width and 0 <= ny < level.height and grid[ny][nx] in ".S":
                    inner += 1
            if inner == 0 or (x in (0, level.width - 1) and y in (0, level.height - 1)):
                continue
            grid[y][x] = "E"
            other = level.__class__(
                level.id, level.name, level.difficulty, tuple("".join(r) for r in grid)
            )
            assert shortest_path_length(other) <= best


def test_border_exit_and_random_start_together():
    level = generate_maze(4, 9, random_start=True, border_exit=True)
    assert level.id == "gen-9-4-r-b"
    assert on_border(level)
    assert level.start == generate_maze(4, 9, random_start=True).start


def test_defaults_keep_the_old_mazes():
    assert generate_maze(3, 9) == generate_maze(3, 9, random_start=False, border_exit=False)


# ---- pools ----


def test_border_exit_pools_hold_the_same_mazes_as_the_plain_ones():
    plain = build_pools(9, 1, 30, 10, 10)
    varied = build_pools(9, 1, 30, 10, 10, random_start=True, border_exit=True)
    for split in ("train", "validation", "test"):
        assert [walls(a) for a in getattr(plain, split)] == [
            walls(b) for b in getattr(varied, split)
        ]
        for level in getattr(varied, split):
            assert on_border(level)
    layouts = set()
    for split in ("train", "validation", "test"):
        for level in getattr(varied, split):
            layouts.add(walls(level))
    assert len(layouts) == 50  # no maze in two pools


# ---- config ----


def test_both_are_off_by_default_and_must_be_bools():
    settings = ConfigFile.model_validate(generated()).levels.generated
    assert settings.border_exit is False and settings.random_start is False
    with pytest.raises(ValidationError, match="border_exit"):
        ConfigFile.model_validate(generated(border_exit="yes"))


def test_config_pools_use_them():
    pools = ConfigFile.model_validate(
        generated(border_exit=True, random_start=True)
    ).resolve_pools()
    for level in pools.train + pools.validation + pools.test:
        assert on_border(level) and level.id.endswith("-r-b")


def test_pool_settings_leave_out_the_defaults_so_older_brains_still_match():
    # brains exported before 2026-11-24 recorded {size, maze_seed, train, validation, test}
    old = {"size": 9, "maze_seed": 1, "train": 6, "validation": 3, "test": 3}
    assert ConfigFile.model_validate(generated()).pool_settings() == old
    assert ConfigFile.model_validate(generated(random_start=False)).pool_settings() == old
    with_exit = ConfigFile.model_validate(generated(border_exit=True)).pool_settings()
    assert with_exit == {**old, "border_exit": True}


def test_shaping_works_with_an_exit_in_the_border():
    level = generate_maze(2, 9, border_exit=True)
    phi = potential(level)
    assert phi[level.exit] == 0.0 and phi[level.start] < 0.0


def test_training_on_border_exit_mazes_records_them(tmp_path):
    from minotaurus.brain import load_brain

    config = ConfigFile.model_validate(generated(border_exit=True))
    pools = config.resolve_pools()
    run_dir = train(config, pools.train, run_dir=tmp_path / "r", pools=pools)
    saved = json.loads(load_brain(run_dir / "brain.onnx").meta["pools"])
    assert saved["border_exit"] is True
    assert json.loads((run_dir / "scores.json").read_text())["test"] >= 0.0
