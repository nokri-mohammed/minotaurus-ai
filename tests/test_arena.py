import asyncio

import pytest

from minotaurus.brain import BrainError
from minotaurus.engine.levels import load_level_by_id
from minotaurus.server.arena import run_arena
from minotaurus.server.messages import ErrorMessage, Result, RunStarted, Tick


def collect(level, brain, tick_seconds=0.0):
    async def gather():
        messages = []
        async for message in run_arena(level, brain, tick_seconds=tick_seconds):
            messages.append(message)
        return messages

    return asyncio.run(gather())


def always_right(obs):
    return 3  # RIGHT


def test_run_starts_ticks_and_finishes(corridor):
    messages = collect(corridor, always_right)
    assert isinstance(messages[0], RunStarted)
    assert messages[0].level_id == corridor.id
    assert (messages[0].start.x, messages[0].start.y) == corridor.start
    ticks = [m for m in messages if isinstance(m, Tick)]
    assert [t.n for t in ticks] == [1, 2]
    assert (ticks[-1].x, ticks[-1].y) == corridor.exit
    result = messages[-1]
    assert isinstance(result, Result)
    assert (result.status, result.steps) == ("finished", 2)
    assert result.seconds == pytest.approx(0.2)


def test_run_times_out_at_the_step_limit(corridor):
    def always_up(obs):
        return 0  # UP, into the wall

    messages = collect(corridor, always_up)
    result = messages[-1]
    assert result.status == "timed_out"
    assert result.steps == corridor.step_limit


def test_a_brain_that_raises_ends_the_run_with_error(corridor):
    def broken(obs):
        raise BrainError("brain is too slow: a step took more than 0.05 s")

    messages = collect(corridor, broken)
    result = messages[-1]
    assert isinstance(result, Result)
    assert result.status == "error"
    assert result.steps == 0
    assert "too slow" in result.message


def test_a_brain_that_returns_a_bad_move_ends_the_run_with_error(corridor):
    messages = collect(corridor, lambda obs: 9)
    assert messages[-1].status == "error"


def test_the_real_level_finishes_in_the_shortest_path_with_a_scripted_brain():
    level = load_level_by_id("easy-01")
    moves = iter([1, 1, 1, 1, 3, 3, 3, 3, 1, 1, 3, 3, 3])  # DOWN x4, RIGHT x4, DOWN x2, RIGHT x3
    messages = collect(level, lambda obs: next(moves))
    assert messages[-1].status == "finished"
    assert messages[-1].steps == 13


def test_error_message_type_exists():
    assert ErrorMessage(type="error", message="x").message == "x"


def test_finished_result_has_a_path_ratio_of_one_on_the_shortest_path(corridor):
    result = collect(corridor, always_right)[-1]
    assert result.path_ratio == 1.0


def test_a_detour_gives_a_path_ratio_above_one(corridor):
    moves = iter([2, 3, 3])  # left (bumps into the wall), right, right

    def wanderer(obs):
        return next(moves)

    result = collect(corridor, wanderer)[-1]
    assert (result.status, result.steps) == ("finished", 3)
    assert result.path_ratio == 1.5  # 3 steps, the shortest path is 2


def test_a_run_that_does_not_finish_has_no_path_ratio(corridor):
    def always_up(obs):
        return 0

    result = collect(corridor, always_up)[-1]
    assert result.status == "timed_out"
    assert result.path_ratio is None
