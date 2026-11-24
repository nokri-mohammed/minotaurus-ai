"""novelty_bonus and revisit_penalty (2026-11-24): training-only rewards from the visit counts."""

import json

import pytest
from pydantic import ValidationError

from minotaurus.engine import MazeEnv
from minotaurus.engine.env import LEFT, RIGHT, UP
from minotaurus.trainer import shaping
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.train import train
from tests.test_trainer import small_dqn_config, small_qtable_config


def random_dqn(episodes: int = 6) -> dict:
    """A DQN that only moves at random (epsilon stays 1): the same moves whatever the rewards."""
    data = small_dqn_config(episodes)
    data["dqn"]["epsilon_start"] = 1.0
    data["dqn"]["epsilon_end"] = 1.0
    data["dqn"]["epsilon_decay"] = 1.0
    return data


def mean_reward(run_dir) -> float:
    rows = []
    for text in (run_dir / "metrics.jsonl").read_text().splitlines():
        row = json.loads(text)
        if "avg_reward" in row:
            rows.append(row["avg_reward"])
    return sum(rows) / len(rows)


# ---- config ----


def test_both_are_zero_by_default_and_recorded():
    config = ConfigFile.model_validate(small_dqn_config())
    assert config.dqn.novelty_bonus == 0.0 and config.dqn.revisit_penalty == 0.0
    options = config.training_options(None)
    assert options["novelty_bonus"] == 0.0 and options["revisit_penalty"] == 0.0
    qtable = ConfigFile.model_validate(small_qtable_config()).training_options(None)
    assert qtable["novelty_bonus"] is None and qtable["revisit_penalty"] is None


@pytest.mark.parametrize("key", ["novelty_bonus", "revisit_penalty"])
def test_they_cannot_be_negative(key):
    data = small_dqn_config()
    data["dqn"][key] = -0.01
    with pytest.raises(ValidationError, match=key):
        ConfigFile.model_validate(data)


def test_they_live_in_the_dqn_block_only():
    data = small_qtable_config()
    data["qtable"]["novelty_bonus"] = 0.02
    with pytest.raises(ValidationError, match="novelty_bonus"):
        ConfigFile.model_validate(data)


def test_they_are_not_agent_arguments():
    data = small_dqn_config()
    data["dqn"]["novelty_bonus"] = 0.02
    data["dqn"]["revisit_penalty"] = 0.01
    params = ConfigFile.model_validate(data).params
    assert "novelty_bonus" not in params and "revisit_penalty" not in params


# ---- the reward ----


def test_visit_reward_from_the_count_before_the_step():
    assert shaping.visit_reward(0, 0.02, 0.01) == pytest.approx(0.02)  # a new square: the bonus
    assert shaping.visit_reward(1, 0.02, 0.01) == pytest.approx(-0.01)  # visited once before
    assert shaping.visit_reward(3, 0.02, 0.01) == pytest.approx(-0.03)  # no cap on the penalty
    assert shaping.visit_reward(5, 0.0, 0.0) == 0.0


def test_count_before_the_step_counts_a_bump_as_a_revisit(corridor):
    env = MazeEnv(corridor)
    env.reset()
    env.step(RIGHT)
    assert shaping.visits_before(env) == 0  # (2,1) was new
    env.step(LEFT)
    assert shaping.visits_before(env) == 1  # back on the start, walked on once before
    env.step(UP)
    assert shaping.visits_before(env) == 2  # a bump: the start again, now for the third time


# ---- the training loop applies them (training only) ----


def test_training_adds_the_bonus_and_the_penalty(tmp_path):
    plain = ConfigFile.model_validate(random_dqn())
    base = mean_reward(train(plain, plain.resolve_levels(), run_dir=tmp_path / "plain"))
    data = random_dqn()
    data["dqn"]["novelty_bonus"] = 0.5
    bonus = ConfigFile.model_validate(data)
    assert mean_reward(train(bonus, bonus.resolve_levels(), run_dir=tmp_path / "bonus")) > base
    data = random_dqn()
    data["dqn"]["revisit_penalty"] = 0.5
    penalty = ConfigFile.model_validate(data)
    assert mean_reward(train(penalty, penalty.resolve_levels(), run_dir=tmp_path / "pen")) < base


def test_the_brain_records_them(tmp_path):
    from minotaurus.brain import load_brain

    data = random_dqn(2)
    data["dqn"]["novelty_bonus"] = 0.02
    data["dqn"]["revisit_penalty"] = 0.01
    config = ConfigFile.model_validate(data)
    run_dir = train(config, config.resolve_levels(), run_dir=tmp_path / "r")
    training = json.loads(load_brain(run_dir / "brain.onnx").meta["training"])
    assert training["novelty_bonus"] == 0.02 and training["revisit_penalty"] == 0.01
