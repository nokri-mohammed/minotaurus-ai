import json
from pathlib import Path

from minotaurus.engine.levels import TEST_MAZE_DIR, load_test_mazes
from minotaurus.engine.pools import walls
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.test_mazes import EXAMPLE_CONFIG, pick_test_mazes

ROOT = Path(__file__).resolve().parents[1]


def example_pools():
    config = ConfigFile.model_validate_json(EXAMPLE_CONFIG.read_text())
    return config.resolve_pools()


def test_the_example_config_has_mixed_sizes_that_fit():
    pools = example_pools()
    assert (len(pools.train), len(pools.validation), len(pools.test)) == (600, 120, 120)
    assert {level.width for level in pools.train} == {9, 11, 13}


def test_pick_takes_the_first_few_of_each_size_in_order():
    picked = pick_test_mazes(example_pools(), per_size=4)
    assert [level.width for level in picked] == [9] * 4 + [11] * 4 + [13] * 4
    assert picked[0].id == "test-09-01" and picked[-1].id == "test-13-04"


def test_the_saved_files_are_the_start_of_the_test_pile():
    expected = pick_test_mazes(example_pools(), per_size=4)
    saved = load_test_mazes()
    assert [lv.id for lv in saved] == [lv.id for lv in expected]
    for saved_level, level in zip(saved, expected, strict=True):
        assert saved_level.grid == level.grid
        assert saved_level.difficulty == level.difficulty


def test_no_saved_test_maze_is_in_the_train_or_validation_pile():
    pools = example_pools()
    used = set()
    for pool in (pools.train, pools.validation):
        for level in pool:
            used.add(walls(level))
    for level in load_test_mazes():
        assert walls(level) not in used


def test_the_files_are_plain_level_files():
    for path in sorted(TEST_MAZE_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        assert set(data) == {"id", "name", "difficulty", "grid"}
