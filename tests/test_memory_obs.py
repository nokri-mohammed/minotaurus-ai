"""obs_version 2: version 1 plus the last move, a bump flag, and visit counts up to 8."""

import numpy as np

from minotaurus.engine import MazeEnv
from minotaurus.engine.env import DOWN, LEFT, RIGHT
from minotaurus.engine.observe import (
    OBS_VERSION,
    OBS_VERSION_MEMORY,
    VISIT_CAP_MEMORY,
    obs_bounds,
    obs_size,
    observe,
)
from minotaurus.engine.race import Race

from .conftest import make_level

N = 25


def small_level():
    return make_level(["#####", "#S..#", "#...#", "#..E#", "#####"])


def test_version_1_is_unchanged_and_version_2_is_five_numbers_longer():
    assert OBS_VERSION == 1
    assert obs_size(5, 1) == 77
    assert obs_size(5, OBS_VERSION_MEMORY) == 82
    low, high = obs_bounds(5, OBS_VERSION_MEMORY)
    assert len(low) == len(high) == 82
    assert high[2 * N] == VISIT_CAP_MEMORY
    assert high[77] == 1.0


def test_the_first_77_numbers_match_version_1_until_a_square_is_visited_more_than_3_times():
    level = small_level()
    visits = {level.start: 2}
    one = observe(level, level.start, visits, 5, 1)
    two = observe(level, level.start, visits, 5, OBS_VERSION_MEMORY)
    assert np.array_equal(one, two[:77])


def test_memory_is_empty_before_the_first_move():
    env = MazeEnv(small_level(), obs_version=OBS_VERSION_MEMORY)
    obs, _ = env.reset()
    assert obs.shape == (82,)
    assert list(obs[77:82]) == [0.0, 0.0, 0.0, 0.0, 0.0]


def test_memory_shows_the_last_move_and_a_bump():
    env = MazeEnv(small_level(), obs_version=OBS_VERSION_MEMORY)
    env.reset()
    obs, *_ = env.step(RIGHT)  # a free move
    assert list(obs[77:82]) == [0.0, 0.0, 0.0, 1.0, 0.0]
    obs, *_ = env.step(DOWN)
    assert list(obs[77:82]) == [0.0, 1.0, 0.0, 0.0, 0.0]
    obs, *_ = env.step(LEFT)
    obs, *_ = env.step(LEFT)  # into the wall: a bump
    assert list(obs[77:82]) == [0.0, 0.0, 1.0, 0.0, 1.0]


def test_visit_counts_go_up_to_8_in_version_2_and_3_in_version_1():
    level = small_level()
    visits = {level.start: 20}
    centre = 2 * N + 12
    assert observe(level, level.start, visits, 5, 1)[centre] == 3.0
    assert observe(level, level.start, visits, 5, OBS_VERSION_MEMORY)[centre] == 8.0


def test_a_reset_forgets_the_last_move():
    env = MazeEnv(small_level(), obs_version=OBS_VERSION_MEMORY)
    env.reset()
    env.step(RIGHT)
    obs, _ = env.reset()
    assert list(obs[77:82]) == [0.0] * 5


def test_a_race_shows_each_dot_its_own_memory():
    race = Race(small_level(), obs_version=OBS_VERSION_MEMORY)
    race.tick([RIGHT, DOWN])
    assert list(race.observation(0)[77:82]) == [0.0, 0.0, 0.0, 1.0, 0.0]
    assert list(race.observation(1)[77:82]) == [0.0, 1.0, 0.0, 0.0, 0.0]
