import pytest

from minotaurus.engine.generate import MAX_SIZE, MIN_SIZE, generate_maze
from minotaurus.engine.levels import LevelError, _validator, shortest_path_length
from minotaurus.engine.pools import build_pools, walls


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


# ---- every size, random start, cached schema ----

# 5 x 5 is left out: it has only 2 wall layouts, too few for three pools (tested below)
ODD_SIZES = range(MIN_SIZE + 2, MAX_SIZE + 1, 2)


def _pool_counts(size: int) -> tuple[int, int, int]:
    # 7 x 7 has only 14 wall layouts, so it gets small pools
    if size == 7:
        return (4, 2, 2)
    return (8, 4, 4)


@pytest.mark.parametrize("random_start", [False, True])
@pytest.mark.parametrize("size", ODD_SIZES)
def test_no_wall_layout_is_in_two_pools_at_any_size(size, random_start):
    train, validation, test = _pool_counts(size)
    pools = build_pools(size, 1, train, validation, test, random_start=random_start)
    seen = {}
    for name, levels in (
        ("train", pools.train),
        ("validation", pools.validation),
        ("test", pools.test),
    ):
        for level in levels:
            layout = walls(level)
            assert layout not in seen, (
                f"{size}x{size}: a {name} maze has the walls of a {seen[layout]} maze"
            )
            seen[layout] = name


def test_random_start_does_not_turn_the_same_walls_into_new_mazes():
    # 5 x 5 has 2 wall layouts but 14 grids once the start moves: still too few for three pools
    with pytest.raises(LevelError, match="different mazes"):
        build_pools(size=5, maze_seed=1, train=1, validation=1, test=1, random_start=True)


def test_start_is_top_left_unless_asked():
    for seed in range(10):
        level = generate_maze(seed, 11)
        assert level.start == (1, 1)
        assert level.id == f"gen-11-{seed}"
        assert generate_maze(seed, 11, random_start=False) == level


def test_default_pools_did_not_change():
    # the walls key gives the same pools as the old grid key when the start is fixed
    pools = build_pools(size=9, maze_seed=1, train=8, validation=4, test=4)
    for level in (*pools.train, *pools.validation, *pools.test):
        assert level.start == (1, 1)
    grids = set()
    for level in (*pools.train, *pools.validation, *pools.test):
        grids.add(level.grid)
    assert len(grids) == 16


def test_random_start_keeps_the_walls_and_moves_the_start():
    starts = set()
    for seed in range(20):
        fixed = generate_maze(seed, 11)
        moved = generate_maze(seed, 11, random_start=True)
        assert walls(moved) == walls(fixed)
        assert moved.id == f"gen-11-{seed}-r"
        assert moved == generate_maze(seed, 11, random_start=True)
        assert shortest_path_length(moved) >= 1
        starts.add(moved.start)
    assert len(starts) > 1


def test_random_start_pools_are_repeatable():
    a = build_pools(size=9, maze_seed=2, train=5, validation=2, test=2, random_start=True)
    b = build_pools(size=9, maze_seed=2, train=5, validation=2, test=2, random_start=True)
    assert a == b


def test_level_schema_is_read_once():
    assert _validator("level.schema.json") is _validator("level.schema.json")
