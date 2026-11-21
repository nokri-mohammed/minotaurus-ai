from minotaurus.engine.env import DOWN, RIGHT, UP
from minotaurus.engine.race import TICK_SECONDS, Race

from .conftest import make_level


def always(action):
    return lambda obs: action


def test_both_start_on_same_square(open_room):
    race = Race(open_room)
    assert race.positions == [open_room.start, open_room.start]


def test_moves_apply_at_once(open_room):
    race = Race(open_room)
    race.tick([RIGHT, DOWN])
    assert race.positions == [(2, 1), (1, 2)]
    assert race.log == [[RIGHT, DOWN]]


def test_wall_bump_in_race(corridor):
    race = Race(corridor)
    race.tick([UP, RIGHT])
    assert race.positions == [(1, 1), (2, 1)]


def test_dots_do_not_block(corridor):
    race = Race(corridor)
    race.tick([RIGHT, RIGHT])
    assert race.positions[0] == race.positions[1] == (2, 1)


def test_winner(corridor):
    race = Race(corridor)
    result = race.run([always(RIGHT), always(UP)])
    assert result.winner == 0 and not result.draw
    assert result.finished == [True, False]
    assert result.ticks == [2, None]
    assert result.seconds[0] == 2 * TICK_SECONDS and result.seconds[1] is None


def test_draw_when_both_arrive_same_tick(corridor):
    result = Race(corridor).run([always(RIGHT), always(RIGHT)])
    assert result.draw and result.winner is None
    assert result.finished == [True, True]
    assert result.ticks == [2, 2]


def test_step_limit_nobody_finishes(corridor):
    result = Race(corridor).run([always(UP), always(UP)])
    assert result.winner is None and not result.draw
    assert result.finished == [False, False]
    assert result.total_ticks == corridor.step_limit
    assert len(result.log) == corridor.step_limit


def test_visited_tracked_per_dot_and_fed_to_brains():
    level = make_level(["#######", "#S...E#", "#######"])
    seen = []

    def spy(obs):
        seen.append(obs.copy())
        return RIGHT

    Race(level).run([spy, always(UP)])
    # window layer "visited" (index 50..74): the dot's own square is marked on tick 1
    assert seen[0].shape == (77,)
    assert seen[0][50 + 12] == 1.0


def test_tick_after_end_raises(corridor):
    race = Race(corridor)
    race.run([always(RIGHT), always(RIGHT)])
    import pytest

    with pytest.raises(RuntimeError):
        race.tick([RIGHT, RIGHT])
