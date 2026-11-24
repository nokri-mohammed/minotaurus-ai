"""Visited layer as a visit count (obs_version 1, 2026-11-24): min(visits, 3) as a raw number."""

import warnings

import numpy as np
import pytest
from typer.testing import CliRunner

from minotaurus.brain import BrainWarning, load_brain
from minotaurus.cli import app
from minotaurus.engine import MazeEnv
from minotaurus.engine.env import DOWN, LEFT, RIGHT, UP
from minotaurus.engine.levels import load_level_by_id
from minotaurus.engine.observe import VISIT_CAP, observe
from minotaurus.engine.race import Race
from minotaurus.trainer.dqn import DQNAgent
from minotaurus.trainer.export import export_dqn, export_qtable
from minotaurus.trainer.qtable import QTableAgent, obs_key
from tests.test_trainer import make_model

from .conftest import make_level

N = 25  # squares in the 5 x 5 window
VISITED = slice(2 * N, 3 * N)
CENTRE = 2 * N + 12  # the dot's own square in the visited layer


def visited_layer(obs):
    return obs[VISITED].reshape(5, 5)


# ---- observe ----


def test_counts_are_raw_numbers_capped_at_three(open_room):
    # dot at (3,2): window x 1..5, y 0..4
    counts = {(3, 2): 1, (2, 2): 2, (1, 1): 7}
    layer = visited_layer(observe(open_room, (3, 2), counts))
    assert layer[2, 2] == 1.0  # visited once stays 1.0
    assert layer[2, 1] == 2.0
    assert layer[1, 0] == VISIT_CAP == 3
    assert layer.sum() == 6.0


def test_a_set_still_means_visited_once(open_room):
    as_set = observe(open_room, (3, 2), {(3, 2), (2, 2), (1, 1)})
    as_counts = observe(open_room, (3, 2), {(3, 2): 1, (2, 2): 1, (1, 1): 1})
    np.testing.assert_array_equal(as_set, as_counts)


# ---- MazeEnv ----


def test_env_counts_moves_and_bumps(corridor):
    env = MazeEnv(corridor)  # S . . E in one row; the start is (1,1)
    obs, _ = env.reset()
    assert env.visits == {(1, 1): 1}
    obs, *_ = env.step(RIGHT)
    assert env.visits[(2, 1)] == 1
    obs, *_ = env.step(LEFT)  # back to the start
    assert env.visits[(1, 1)] == 2 and obs[CENTRE] == 2.0
    obs, *_ = env.step(UP)  # a bump: the dot stays, and this counts as one more visit
    assert env.visits[(1, 1)] == 3 and obs[CENTRE] == 3.0
    obs, *_ = env.step(DOWN)  # another bump: the count goes on, the input stays at the cap
    assert env.visits[(1, 1)] == 4 and obs[CENTRE] == 3.0
    assert env.visited == {(1, 1), (2, 1)}  # the squares walked on, as before


def test_old_input_is_unchanged_until_a_square_is_revisited():
    level = load_level_by_id("easy-01")
    env = MazeEnv(level)
    obs, _ = env.reset()
    walked = {env.pos}
    for action in (DOWN, DOWN, DOWN, DOWN):  # (1,1) down to (1,5): new squares only
        obs, *_ = env.step(action)
        walked.add(env.pos)
        np.testing.assert_array_equal(obs, observe(level, env.pos, walked))
    obs, *_ = env.step(UP)  # back onto (1,4): a revisit, now the input differs
    assert obs[CENTRE] == 2.0
    assert observe(level, env.pos, walked)[CENTRE] == 1.0


def test_observation_space_bounds_and_every_observation_fits():
    env = MazeEnv(load_level_by_id("easy-01"))
    low, high = env.observation_space.low, env.observation_space.high
    assert low[: 3 * N].tolist() == [0.0] * (3 * N) and low[3 * N :].tolist() == [-1.0, -1.0]
    assert high[: 2 * N].tolist() == [1.0] * (2 * N)
    assert high[VISITED].tolist() == [float(VISIT_CAP)] * N
    assert high[3 * N :].tolist() == [1.0, 1.0]
    rng = np.random.default_rng(5)
    obs, _ = env.reset()
    for _ in range(200):  # random walk with many bumps and revisits
        assert env.observation_space.contains(obs)
        obs, _, term, trunc, _ = env.step(int(rng.integers(4)))
        if term or trunc:
            obs, _ = env.reset()


# ---- Race ----


def test_race_counts_each_dot_on_its_own():
    level = make_level(["#######", "#S...E#", "#######"])
    race = Race(level)
    race.tick([UP, RIGHT])  # dot 0 bumps and stays on the start, dot 1 moves on
    assert race.observation(0)[CENTRE] == 2.0
    assert race.observation(1)[CENTRE] == 1.0
    assert race.visits[0] == {(1, 1): 2}


# ---- exported brains and the loader ----


def test_exported_brains_say_their_visited_layer_is_counts(tmp_path):
    export_qtable(QTableAgent(0.1, 0.9, 1.0, 0.1, 0.9), tmp_path / "q.onnx", "q", ["easy-01"])
    agent = DQNAgent([8], 0.01, 8, 0.9, 100, 10, 1.0, 0.05, 0.9)
    export_dqn(agent, tmp_path / "d.onnx", "d", ["easy-01"])
    for name in ("q.onnx", "d.onnx"):
        with warnings.catch_warnings():
            warnings.simplefilter("error", BrainWarning)  # a new brain gives no warning
            brain = load_brain(tmp_path / name)
        assert brain.meta["visited"] == "counts"
        assert brain.visited_counts is True


def test_loader_warns_but_accepts_a_brain_without_visited_counts(tmp_path):
    with pytest.warns(BrainWarning, match="yes/no"):
        brain = load_brain(make_model(tmp_path))
    assert brain.visited_counts is False
    assert brain(np.zeros(77, dtype=np.float32)) in range(4)


def test_check_brain_shows_the_warning(tmp_path):
    result = CliRunner().invoke(app, ["check-brain", str(make_model(tmp_path))])
    assert result.exit_code == 0
    assert "WARNING" in result.output and "yes/no" in result.output
    assert "OK:" in result.output


# ---- Q-table: the key keeps the yes/no visited layer ----


def with_counts(obs: np.ndarray, value: float) -> np.ndarray:
    """A copy of `obs` where every visited square shows `value` instead of 1."""
    out = obs.copy()
    for i in range(2 * N, 3 * N):
        if out[i] > 0:
            out[i] = value
    return out


def test_qtable_key_treats_any_count_as_visited():
    env = MazeEnv(load_level_by_id("easy-01"))
    obs, _ = env.reset()
    obs, *_ = env.step(DOWN)
    assert obs[VISITED].max() == 1.0
    for value in (2.0, 3.0):
        assert obs_key(with_counts(obs, value)) == obs_key(obs)
    unvisited = obs.copy()
    unvisited[VISITED] = 0.0
    assert obs_key(unvisited) != obs_key(obs)  # visited or not still matters


def test_exported_qtable_reads_counts_as_visited(tmp_path):
    env = MazeEnv(load_level_by_id("easy-01"))
    obs, _ = env.reset()
    obs, *_ = env.step(DOWN)
    agent = QTableAgent(0.1, 0.9, 1.0, 0.1, 0.9)
    agent.q[obs_key(obs)] = np.array([0.1, 0.9, 0.2, 0.3], dtype=np.float32)
    export_qtable(agent, tmp_path / "q.onnx", "q", ["easy-01"])
    brain = load_brain(tmp_path / "q.onnx")
    np.testing.assert_array_equal(brain.scores(obs), agent.q[obs_key(obs)])
    for value in (2.0, 3.0):
        counted = with_counts(obs, value)
        np.testing.assert_array_equal(brain.scores(counted), brain.scores(obs))
        np.testing.assert_array_equal(agent.scores(counted), agent.scores(obs))
