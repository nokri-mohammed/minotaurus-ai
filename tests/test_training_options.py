"""Training options: step limit, curriculum, best-on-validation export, recorded settings."""

import json

import pytest
from pydantic import ValidationError

from minotaurus.engine.levels import DEFAULT_STEP_LIMIT_FACTOR, load_level_by_id
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.train import train, training_copies
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
