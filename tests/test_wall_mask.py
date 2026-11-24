"""wall_mask (2026-11-24): never pick a move into a wall the dot can see, in training and play."""

import json

import numpy as np
import pytest
import torch
from fastapi.testclient import TestClient
from pydantic import ValidationError

from minotaurus.brain import BrainError, load_brain, player
from minotaurus.engine import MazeEnv
from minotaurus.engine.env import DOWN, LEFT, RIGHT, UP
from minotaurus.engine.levels import load_level_by_id
from minotaurus.engine.observe import blocked_moves, free_moves
from minotaurus.server.app import create_app
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.dqn import DQNAgent, best_next_values
from minotaurus.trainer.export import export_qtable
from minotaurus.trainer.qtable import QTableAgent, obs_key
from minotaurus.trainer.train import train
from tests.test_server import run_messages, upload
from tests.test_trainer import small_dqn_config, small_qtable_config


def start_obs(level_id: str = "easy-01") -> np.ndarray:
    obs, _ = MazeEnv(load_level_by_id(level_id)).reset()
    return obs


def untrained_brain(tmp_path, meta: dict | None = None, name: str = "b.onnx"):
    """An untrained Q-table: every score is 0, so without a mask it always picks move 0 (up)."""
    path = tmp_path / name
    export_qtable(QTableAgent(0.1, 0.9, 1.0, 0.1, 0.9), path, "t", ["easy-01"], extra_meta=meta)
    return path


# ---- which moves are blocked ----


def test_blocked_moves_reads_the_walls_next_to_the_dot(corridor):
    obs, _ = MazeEnv(corridor).reset()  # start (1,1): wall above, below and to the left
    assert blocked_moves(obs) == [True, True, True, False]  # up, down, left, right
    assert free_moves(obs) == [RIGHT]


def test_easy_01_start_has_two_free_moves():
    # easy-01 start (1,1): wall above and to the left, floor below and to the right
    assert free_moves(start_obs()) == [DOWN, RIGHT]


# ---- config ----


def test_wall_mask_is_off_by_default_and_recorded():
    config = ConfigFile.model_validate(small_qtable_config())
    assert config.wall_mask is False
    assert config.training_options(None)["wall_mask"] is False
    data = small_qtable_config()
    data["wall_mask"] = True
    assert ConfigFile.model_validate(data).training_options(None)["wall_mask"] is True


def test_wall_mask_must_be_a_bool():
    data = small_qtable_config()
    data["wall_mask"] = "yes"
    with pytest.raises(ValidationError, match="wall_mask"):
        ConfigFile.model_validate(data)


# ---- agents ----


@pytest.mark.parametrize("make", ["qtable", "dqn"])
def test_agents_with_the_mask_never_pick_a_wall(make):
    if make == "qtable":
        agent = QTableAgent(0.1, 0.9, 1.0, 1.0, 1.0, seed=3, wall_mask=True)
    else:
        agent = DQNAgent([8], 0.01, 8, 0.9, 100, 10, 1.0, 1.0, 1.0, seed=3, wall_mask=True)
    obs = start_obs()
    for _ in range(200):  # epsilon 1: every move is random, and still never into a wall
        assert agent.act(obs) in (DOWN, RIGHT)
    agent.epsilon = 0.0
    assert agent.act(obs) in (DOWN, RIGHT)


def test_greedy_choice_skips_a_wall_even_with_the_best_score():
    obs = start_obs()
    for mask in (False, True):
        agent = QTableAgent(0.1, 0.9, 0.0, 0.0, 1.0, wall_mask=mask)
        agent.q[obs_key(obs)] = np.array([9.0, 1.0, 5.0, 2.0], dtype=np.float32)  # up is best
        assert agent.act(obs, explore=False) == (RIGHT if mask else UP)


def test_without_the_mask_random_moves_are_unchanged():
    plain = QTableAgent(0.1, 0.9, 1.0, 1.0, 1.0, seed=7)
    obs = start_obs()
    chosen = [plain.act(obs) for _ in range(50)]
    assert UP in chosen and LEFT in chosen  # walls are still picked without the mask


def test_qtable_target_uses_only_free_moves_of_the_next_square():
    obs = start_obs()
    nxt = start_obs()  # the same square: up and left are walls there
    for mask, expected in ((False, 9.0), (True, 2.0)):
        agent = QTableAgent(1.0, 1.0, 0.0, 0.0, 1.0, wall_mask=mask)
        agent.q[obs_key(nxt)] = np.array([9.0, 1.0, 9.0, 2.0], dtype=np.float32)
        agent.update(obs, RIGHT, 0.0, nxt, False)  # learning rate 1, gamma 1: Q = best next
        assert agent.q[obs_key(obs)][RIGHT] == expected


def test_dqn_target_uses_only_free_moves_of_the_next_square():
    nxt = torch.as_tensor(np.stack([start_obs(), start_obs()]))
    q = torch.tensor([[9.0, 1.0, 9.0, 2.0], [0.0, 4.0, 0.0, 3.0]])
    assert best_next_values(q, nxt, wall_mask=False).tolist() == [9.0, 4.0]
    assert best_next_values(q, nxt, wall_mask=True).tolist() == [2.0, 4.0]


# ---- training writes it into the brain ----


@pytest.mark.parametrize("config", ["qtable", "dqn"])
def test_training_with_the_mask_marks_the_brain(tmp_path, config):
    data = small_qtable_config(5) if config == "qtable" else small_dqn_config(3)
    data["wall_mask"] = True
    config = ConfigFile.model_validate(data)
    run_dir = train(config, config.resolve_levels(), run_dir=tmp_path / "run")
    brain = load_brain(run_dir / "brain.onnx")
    assert brain.wall_mask is True
    assert brain.meta["wall_mask"] == "true"
    assert json.loads(brain.meta["training"])["wall_mask"] is True
    assert json.loads((run_dir / "config.json").read_text())["wall_mask"] is True


def test_training_without_the_mask_writes_nothing(tmp_path):
    config = ConfigFile.model_validate(small_qtable_config(3))
    run_dir = train(config, config.resolve_levels(), run_dir=tmp_path / "run")
    brain = load_brain(run_dir / "brain.onnx")
    assert "wall_mask" not in brain.meta and brain.wall_mask is False


# ---- loader and player ----


def test_loader_reads_the_wall_mask_metadata(tmp_path):
    assert load_brain(untrained_brain(tmp_path, {"wall_mask": "true"})).wall_mask is True
    assert (
        load_brain(untrained_brain(tmp_path, {"wall_mask": "false"}, "f.onnx")).wall_mask is False
    )
    assert load_brain(untrained_brain(tmp_path, None, "n.onnx")).wall_mask is False


def test_loader_refuses_bad_wall_mask_metadata(tmp_path):
    with pytest.raises(BrainError, match="wall_mask"):
        load_brain(untrained_brain(tmp_path, {"wall_mask": "maybe"}))


def test_player_applies_the_brains_own_mask(tmp_path):
    obs = start_obs()
    plain = load_brain(untrained_brain(tmp_path, None, "p.onnx"))
    masked = load_brain(untrained_brain(tmp_path, {"wall_mask": "true"}, "m.onnx"))
    assert player(plain, seed="s")(obs) == UP  # the wall above: a bump
    assert player(masked, seed="s")(obs) == DOWN  # the best free move (all scores are equal)


def test_random_moves_with_the_mask_avoid_walls_too(tmp_path):
    masked = load_brain(untrained_brain(tmp_path, {"wall_mask": "true", "policy_epsilon": "1"}))
    play = player(masked, seed="s")
    obs = start_obs()
    chosen = set()
    for _ in range(100):
        chosen.add(play(obs))
    assert chosen == {DOWN, RIGHT}


def test_the_arena_server_applies_the_mask_per_brain(tmp_path):
    client = TestClient(create_app(tick_seconds=0.0))
    for meta, bumps_expected in ((None, True), ({"wall_mask": "true"}, False)):
        path = untrained_brain(tmp_path, meta, f"{bumps_expected}.onnx")
        assert upload(client, path).status_code == 200
        ticks = [m for m in run_messages(client, "easy-01") if m.type == "tick"]
        stays = 0
        previous = (1, 1)
        for tick in ticks:
            if (tick.x, tick.y) == previous:
                stays += 1
            previous = (tick.x, tick.y)
        assert (stays > 0) is bumps_expected
