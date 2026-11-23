"""Potential-based reward shaping: training only, off by default."""

import asyncio
import json

import pytest

from minotaurus.brain import load_brain
from minotaurus.engine.levels import load_level_by_id
from minotaurus.server.arena import run_arena
from minotaurus.trainer import shaping
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.evaluate import score_brain, success_rate
from minotaurus.trainer.shaping import potential, shaped_reward
from minotaurus.trainer.train import train
from tests.conftest import make_level
from tests.test_trainer import small_dqn_config


def test_potential_is_zero_at_the_exit_and_minus_one_at_the_farthest_square():
    level = make_level(["######", "#S..E#", "######"])
    phi = potential(level)
    assert phi[level.exit] == 0.0
    assert phi[level.start] == -1.0  # the start is the farthest square here: 3 steps
    assert phi[(2, 1)] == pytest.approx(-2 / 3)
    assert phi[(3, 1)] == pytest.approx(-1 / 3)
    assert (0, 0) not in phi  # walls have no potential


def test_potential_uses_maze_distance_not_straight_line():
    # the exit is 2 squares away in a straight line, but 6 steps round the wall
    level = make_level(["#####", "#S#E#", "#.#.#", "#...#", "#####"])
    phi = potential(level)
    assert phi[level.start] == -1.0
    assert phi[(1, 3)] == pytest.approx(-4 / 6)


def test_shaped_reward_adds_gamma_phi_next_minus_phi_now():
    phi = {(1, 1): -1.0, (2, 1): -0.5}
    reward = shaped_reward(-0.01, phi, (1, 1), (2, 1), gamma=0.9, on_bump=True)
    assert reward == pytest.approx(-0.01 + 0.9 * -0.5 - -1.0)


def test_shaping_on_bump_false_leaves_a_bump_unshaped():
    phi = {(1, 1): -1.0}
    bumped = shaped_reward(-0.05, phi, (1, 1), (1, 1), gamma=0.9, on_bump=False)
    assert bumped == -0.05
    shaped = shaped_reward(-0.05, phi, (1, 1), (1, 1), gamma=0.9, on_bump=True)
    assert shaped == pytest.approx(-0.05 + 0.9 * -1.0 + 1.0)


def test_shaping_is_off_by_default_and_not_an_agent_argument():
    cfg = ConfigFile.model_validate(small_dqn_config())
    assert cfg.dqn.shaping is False and cfg.dqn.shaping_on_bump is True
    on = small_dqn_config()
    on["dqn"]["shaping"] = True
    on["dqn"]["shaping_on_bump"] = False
    cfg = ConfigFile.model_validate(on)
    assert "shaping" not in cfg.params and "shaping_on_bump" not in cfg.params


def test_qtable_has_no_shaping_setting():
    from tests.test_trainer import small_qtable_config

    data = small_qtable_config()
    data["qtable"]["shaping"] = True
    with pytest.raises(Exception, match="shaping"):
        ConfigFile.model_validate(data)


def test_shaping_changes_the_training_rewards_only_when_switched_on(tmp_path):
    plain = ConfigFile.model_validate(small_dqn_config(episodes=6))
    on_data = small_dqn_config(episodes=6)
    on_data["dqn"]["shaping"] = True
    on = ConfigFile.model_validate(on_data)
    levels = plain.resolve_levels()
    a = train(plain, levels, run_dir=tmp_path / "a", log_every=3)
    b = train(plain, levels, run_dir=tmp_path / "b", log_every=3)
    c = train(on, levels, run_dir=tmp_path / "c", log_every=3)
    first_a = json.loads((a / "metrics.jsonl").read_text().splitlines()[0])
    first_b = json.loads((b / "metrics.jsonl").read_text().splitlines()[0])
    first_c = json.loads((c / "metrics.jsonl").read_text().splitlines()[0])
    assert first_a == first_b  # off: the same seed still gives the same run
    assert first_c["avg_reward"] != first_a["avg_reward"]


def test_shaping_never_runs_when_scoring_or_in_the_arena(tmp_path, monkeypatch):
    data = small_dqn_config(episodes=4)
    data["dqn"]["shaping"] = True
    data["levels"] = {
        "generated": {"size": 7, "maze_seed": 5, "train": 4, "validation": 2, "test": 2}
    }
    config = ConfigFile.model_validate(data)
    pools = config.resolve_pools()
    run = train(config, pools.train, run_dir=tmp_path / "r", log_every=2)

    def forbidden(*args, **kwargs):
        raise AssertionError("shaping ran outside training")

    monkeypatch.setattr(shaping, "potential", forbidden)
    monkeypatch.setattr(shaping, "shaped_reward", forbidden)
    brain = load_brain(run / "brain.onnx")
    score_brain(run / "brain.onnx", config, pools)
    success_rate(brain, pools.test)

    async def play():
        async for _ in run_arena(load_level_by_id("easy-01"), brain, tick_seconds=0.0):
            pass

    asyncio.run(play())
