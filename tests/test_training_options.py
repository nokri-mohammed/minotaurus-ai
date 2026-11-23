"""Training options: step limit, curriculum, best-on-validation export, recorded settings."""

import json

import pytest
from pydantic import ValidationError

from minotaurus.engine.levels import DEFAULT_STEP_LIMIT_FACTOR, load_level_by_id
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.train import stage_starts, train, training_copies
from tests.test_trainer import small_qtable_config


def random_walk_config(episodes: int = 3) -> dict:
    """A Q-table that only ever moves at random (epsilon stays at 1)."""
    data = small_qtable_config(episodes)
    data["qtable"]["epsilon_start"] = 1.0
    data["qtable"]["epsilon_end"] = 1.0
    data["qtable"]["epsilon_decay"] = 1.0
    return data


def read_lines(run_dir) -> list[dict]:
    rows = []
    for text in (run_dir / "metrics.jsonl").read_text().splitlines():
        rows.append(json.loads(text))
    return rows


# ---- training step limit ----


def test_train_step_limit_factor_is_unset_by_default():
    assert ConfigFile.model_validate(small_qtable_config()).train_step_limit_factor is None


@pytest.mark.parametrize("bad", [0, -1.0])
def test_train_step_limit_factor_must_be_positive(bad):
    data = small_qtable_config()
    data["train_step_limit_factor"] = bad
    with pytest.raises(ValidationError, match="train_step_limit_factor"):
        ConfigFile.model_validate(data)


def test_training_copies_change_only_the_step_limit():
    level = load_level_by_id("easy-01")  # shortest path 13 steps
    same = training_copies((level,), None)
    assert same == (level,)
    longer = training_copies((level,), 20.0)[0]
    assert longer.step_limit == 20 * 13
    assert (longer.id, longer.grid) == (level.id, level.grid)
    assert level.step_limit_factor == DEFAULT_STEP_LIMIT_FACTOR  # the original is untouched


def test_training_uses_the_training_step_limit(tmp_path):
    # factor 0.5 on easy-01: a limit of 6 steps, too few to reach an exit 13 steps away,
    # so every training episode lasts exactly 6 steps
    data = random_walk_config()
    data["train_step_limit_factor"] = 0.5
    config = ConfigFile.model_validate(data)
    run = train(config, config.resolve_levels(), run_dir=tmp_path / "r", log_every=3)
    assert read_lines(run)[0]["avg_steps"] == 6


def test_scoring_keeps_the_normal_step_limit(tmp_path):
    data = random_walk_config()
    data["train_step_limit_factor"] = 0.5
    data["levels"] = {
        "generated": {"size": 7, "maze_seed": 5, "train": 4, "validation": 2, "test": 2}
    }
    config = ConfigFile.model_validate(data)
    pools = config.resolve_pools()
    train(config, pools.train, run_dir=tmp_path / "r", log_every=3, pools=pools)
    for level in (*pools.train, *pools.validation, *pools.test):
        assert level.step_limit_factor == DEFAULT_STEP_LIMIT_FACTOR


# ---- size curriculum (experimental) ----


def curriculum_config(stages, episodes: int = 9) -> dict:
    data = random_walk_config(episodes)
    data["levels"] = {
        "generated": {"size": 9, "maze_seed": 1, "train": 6, "validation": 2, "test": 2}
    }
    data["stages"] = stages
    return data


def test_stages_are_unset_by_default():
    assert ConfigFile.model_validate(small_qtable_config()).stages is None


@pytest.mark.parametrize(
    "stages",
    [
        [5, 7],  # the last stage must be the pool size (9)
        [5, 8, 9],  # sizes are odd
        [3, 9],  # sizes are 5 to 41
        [9],  # one stage is no curriculum
    ],
)
def test_bad_stages_are_refused(stages):
    with pytest.raises(ValidationError, match="stages"):
        ConfigFile.model_validate(curriculum_config(stages))


def test_stages_need_generated_levels():
    data = small_qtable_config()
    data["stages"] = [5, 7]
    with pytest.raises(ValidationError, match="stages"):
        ConfigFile.model_validate(data)


def test_stage_starts_split_the_episodes_evenly():
    assert stage_starts(5000, 3) == [1, 1667, 3334]
    assert stage_starts(10, 3) == [1, 4, 7]
    assert stage_starts(10, 1) == [1]


def test_resolve_stages_gives_small_mazes_first_and_the_train_pool_last():
    config = ConfigFile.model_validate(curriculum_config([5, 7, 9]))
    pools = config.resolve_pools()
    stages = config.resolve_stages(pools)
    assert stages[-1] == pools.train
    assert {lv.width for lv in stages[0]} == {5}
    assert {lv.width for lv in stages[1]} == {7}
    assert len(stages[0]) == 2  # 5 x 5 has only 2 different mazes
    assert len(stages[1]) == 6  # up to the train pool size
    assert ConfigFile.model_validate(random_walk_config()).resolve_stages(None) is None


def test_training_plays_the_stages_in_order(tmp_path, monkeypatch):
    import minotaurus.trainer.train as train_module

    widths = []

    class SpyEnv(train_module.MazeEnv):
        def reset(self, *, seed=None, options=None):
            widths.append(self.level.width)
            return super().reset(seed=seed, options=options)

    monkeypatch.setattr(train_module, "MazeEnv", SpyEnv)
    config = ConfigFile.model_validate(curriculum_config([5, 7, 9], episodes=9))
    pools = config.resolve_pools()
    train(config, pools.train, run_dir=tmp_path / "r", stages=config.resolve_stages(pools))
    assert widths == [5, 5, 5, 7, 7, 7, 9, 9, 9]
