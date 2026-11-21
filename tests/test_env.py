import numpy as np
from gymnasium.utils.env_checker import check_env

from minotaurus.engine.env import DOWN, LEFT, RIGHT, UP, MazeEnv
from minotaurus.engine.levels import load_level_by_id


def test_gymnasium_checker():
    check_env(MazeEnv(load_level_by_id("easy-01")), skip_render_check=True)


def test_reset_places_dot_and_marks_visited(corridor):
    env = MazeEnv(corridor)
    obs, info = env.reset(seed=1)
    assert env.pos == corridor.start
    assert obs.shape == (77,)
    assert info == {"pos": (1, 1)}
    assert env.visited == {(1, 1)}


def test_move_and_reward(corridor):
    env = MazeEnv(corridor)
    env.reset()
    _, r, term, trunc, _info = env.step(RIGHT)
    assert env.pos == (2, 1)
    assert r == -0.01 and not term and not trunc
    assert (2, 1) in env.visited


def test_wall_bump_stays_and_costs(corridor):
    env = MazeEnv(corridor)
    env.reset()
    _, r, _term, _trunc, info = env.step(UP)
    assert env.pos == (1, 1)
    assert np.isclose(r, -0.05)
    assert info["bumped"] is True
    env.step(LEFT)
    assert env.pos == (1, 1)


def test_exit_terminates_with_bonus(corridor):
    env = MazeEnv(corridor)
    env.reset()
    env.step(RIGHT)
    _, r, term, trunc, _ = env.step(RIGHT)
    assert env.pos == corridor.exit
    assert term and not trunc
    assert np.isclose(r, 1.0)


def test_step_limit_truncates(corridor):
    env = MazeEnv(corridor)  # limit 8
    env.reset()
    for i in range(8):
        _, _, term, trunc, _ = env.step(UP)
        assert not term
        assert trunc == (i == 7)


def test_actions_map(corridor):
    assert (UP, DOWN, LEFT, RIGHT) == (0, 1, 2, 3)


def test_solving_easy_01_by_bfs_path():
    from minotaurus.engine.levels import shortest_path_actions

    level = load_level_by_id("easy-01")
    env = MazeEnv(level)
    env.reset()
    term = False
    for a in shortest_path_actions(level):
        _, _, term, _, _ = env.step(a)
    assert term
