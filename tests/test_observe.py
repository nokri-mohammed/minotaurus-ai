import numpy as np

from minotaurus.engine.observe import OBS_VERSION, obs_size, observe

from .conftest import make_level


def split(vec, window=5):
    n = window * window
    return (
        vec[:n].reshape(window, window),
        vec[n : 2 * n].reshape(window, window),
        vec[2 * n : 3 * n].reshape(window, window),
        vec[3 * n :],
    )


def test_version_and_size():
    assert OBS_VERSION == 1
    assert obs_size(5) == 77
    assert obs_size(3) == 29


def test_shape_dtype(open_room):
    v = observe(open_room, open_room.start, {open_room.start})
    assert v.shape == (77,) and v.dtype == np.float32


def test_walls_outside_maze_count_as_walls(open_room):
    # dot at top-left floor (1,1): window covers x -1..3, y -1..3
    walls, exit_, _visited, _ = split(observe(open_room, (1, 1), {(1, 1)}))
    assert walls[0].tolist() == [1, 1, 1, 1, 1]  # y=-1 row outside
    assert walls[:, 0].tolist() == [1, 1, 1, 1, 1]  # x=-1 column outside
    assert walls[1, 1] == 1  # (0,0) wall tile of the maze
    assert walls[2, 2] == 0  # the dot's own square is floor
    assert exit_.sum() == 0


def test_exit_in_window_and_visited(open_room):
    # dot at (3,2): window x 1..5, y 0..4; exit at (5,3) -> window col 4 row 3
    _walls, exit_, visited, direction = split(observe(open_room, (3, 2), {(1, 1), (3, 2), (2, 2)}))
    assert exit_[3, 4] == 1 and exit_.sum() == 1
    assert visited[2, 2] == 1  # own square
    assert visited[2, 1] == 1  # (2,2)
    assert visited[1, 0] == 1  # (1,1)
    assert visited.sum() == 3
    assert direction.tolist() == [1.0, 1.0]  # exit is right and down


def test_exit_direction_signs(open_room):
    assert split(observe(open_room, (5, 3), set()))[3].tolist() == [0.0, 0.0]
    assert split(observe(open_room, (5, 1), set()))[3].tolist() == [0.0, 1.0]
    assert split(observe(open_room, (1, 3), set()))[3].tolist() == [1.0, 0.0]


def test_exit_outside_window_not_marked(open_room):
    _, exit_, _, direction = split(observe(open_room, (1, 1), {(1, 1)}))
    assert exit_.sum() == 0
    assert direction.tolist() == [1.0, 1.0]


def test_window_param_changes_size(open_room):
    v = observe(open_room, (3, 2), set(), window=3)
    assert v.shape == (obs_size(3),)


def test_exit_left_up():
    level = make_level(["#####", "#E.S#", "#####"])
    assert split(observe(level, level.start, set()))[3].tolist() == [-1.0, 0.0]
