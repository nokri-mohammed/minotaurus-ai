import pytest

from minotaurus.engine.generate import generate_maze
from minotaurus.engine.levels import LevelError, shortest_path_length
from minotaurus.engine.pools import build_pools


def test_same_seed_gives_the_same_maze():
    assert generate_maze(7, 11).grid == generate_maze(7, 11).grid


def test_different_seeds_give_different_mazes():
    assert generate_maze(1, 11).grid != generate_maze(2, 11).grid


def test_maze_is_valid_and_solvable():
    for seed in range(20):
        level = generate_maze(seed, 9)
        assert level.width == 9 and level.height == 9
        assert shortest_path_length(level) >= 1
        assert level.grid[0] == "#" * 9


def test_size_must_be_odd_and_not_tiny():
    with pytest.raises(LevelError, match="size"):
        generate_maze(1, 10)
    with pytest.raises(LevelError, match="size"):
        generate_maze(1, 3)


def test_pools_have_the_asked_sizes():
    pools = build_pools(size=9, maze_seed=1, train=6, validation=3, test=4)
    assert (len(pools.train), len(pools.validation), len(pools.test)) == (6, 3, 4)


def test_no_maze_layout_is_in_two_pools():
    pools = build_pools(size=9, maze_seed=1, train=8, validation=4, test=4)
    train = {lv.grid for lv in pools.train}
    validation = {lv.grid for lv in pools.validation}
    test = {lv.grid for lv in pools.test}
    assert not train & validation
    assert not train & test
    assert not validation & test
    assert len(train) == 8


def test_pools_are_repeatable_and_ids_are_unique():
    a = build_pools(size=9, maze_seed=3, train=5, validation=2, test=2)
    b = build_pools(size=9, maze_seed=3, train=5, validation=2, test=2)
    assert [lv.grid for lv in a.test] == [lv.grid for lv in b.test]
    ids = [lv.id for lv in (*a.train, *a.validation, *a.test)]
    assert len(ids) == len(set(ids))


def test_too_many_mazes_for_a_tiny_size_is_refused():
    with pytest.raises(LevelError, match="different mazes"):
        build_pools(size=5, maze_seed=1, train=50, validation=50, test=50)
