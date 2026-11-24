import json

import pytest

from minotaurus.engine.levels import (
    LevelError,
    load_level,
    load_level_by_id,
    parse_level,
    shortest_path_length,
)

from .conftest import make_level


def test_parse_basic(corridor):
    assert (corridor.width, corridor.height) == (5, 3)
    assert corridor.start == (1, 1)
    assert corridor.exit == (3, 1)
    assert corridor.is_wall(0, 0)
    assert not corridor.is_wall(2, 1)
    assert corridor.is_wall(-1, 1) and corridor.is_wall(1, 9)  # outside counts as wall


def test_shortest_path_and_step_limit(corridor):
    assert shortest_path_length(corridor) == 2
    assert corridor.step_limit == 8  # default factor 4


def test_step_limit_factor():
    level = make_level(["#####", "#S.E#", "#####"], step_limit_factor=10)
    assert level.step_limit == 20


@pytest.mark.parametrize(
    "rows",
    [
        ["#####", "#S.E", "#####"],  # not rectangular
        ["#####", "#...#", "#####"],  # no S and no E
        ["#####", "#SSE#", "#####"],  # two S
        ["#####", "#SEE#", "#####"],  # two E
        ["#####", "#S#E#", "#####"],  # not solvable
        ["#####", "#S.xE#", "#####"],  # bad character
    ],
)
def test_bad_levels_rejected(rows):
    with pytest.raises(LevelError):
        make_level(rows)


def test_bad_difficulty_rejected():
    with pytest.raises(LevelError):
        parse_level({"id": "a", "name": "A", "difficulty": "insane", "grid": ["S.E"]})


def test_missing_field_names_it():
    with pytest.raises(LevelError, match="name"):
        parse_level({"id": "a", "difficulty": "easy", "grid": ["S.E"]})


def test_easy_01_loads_and_is_solvable():
    level = load_level_by_id("easy-01")
    assert level.difficulty == "easy"
    assert (level.width, level.height) == (9, 9)
    assert shortest_path_length(level) > 0


def test_load_level_from_path(tmp_path):
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"id": "x-1", "name": "X", "difficulty": "hard", "grid": ["S.E"]}))
    assert load_level(p).id == "x-1"


def test_unknown_level_id():
    with pytest.raises(LevelError, match="nope"):
        load_level_by_id("nope")


# ---- picking levels from the folder ----


def test_load_all_levels_reads_every_json_file(tmp_path):
    from minotaurus.engine.levels import load_all_levels

    for i, difficulty in enumerate(["easy", "hard"]):
        data = {"id": f"lv-{i}", "name": "L", "difficulty": difficulty, "grid": ["S.E"]}
        (tmp_path / f"lv-{i}.json").write_text(json.dumps(data))
    (tmp_path / "notes.txt").write_text("not a level")
    assert [lv.id for lv in load_all_levels(tmp_path)] == ["lv-0", "lv-1"]


def test_select_by_difficulty():
    from minotaurus.engine.levels import select_by_difficulty

    easy = make_level(["S.E"], difficulty="easy")
    hard = parse_level({"id": "h-01", "name": "H", "difficulty": "hard", "grid": ["S.E"]})
    assert select_by_difficulty([easy, hard], "hard") == (hard,)


def test_select_by_difficulty_none_found():
    from minotaurus.engine.levels import select_by_difficulty

    with pytest.raises(LevelError, match="hard"):
        select_by_difficulty([make_level(["S.E"])], "hard")


def test_select_by_ids_keeps_the_requested_order():
    from minotaurus.engine.levels import select_by_ids

    a = make_level(["S.E"])
    b = parse_level({"id": "b-01", "name": "B", "difficulty": "easy", "grid": ["S.E"]})
    assert select_by_ids([a, b], ["b-01", "t-01"]) == (b, a)


def test_select_by_ids_unknown_id():
    from minotaurus.engine.levels import select_by_ids

    with pytest.raises(LevelError, match="nope-99"):
        select_by_ids([make_level(["S.E"])], ["nope-99"])


def test_load_all_levels_orders_easy_then_medium_then_hard(tmp_path):
    from minotaurus.engine.levels import load_all_levels

    for level_id, difficulty in [("a-hard", "hard"), ("b-easy", "easy"), ("c-medium", "medium")]:
        data = {"id": level_id, "name": "L", "difficulty": difficulty, "grid": ["S.E"]}
        (tmp_path / f"{level_id}.json").write_text(json.dumps(data))
    assert [lv.id for lv in load_all_levels(tmp_path)] == ["b-easy", "c-medium", "a-hard"]


def test_each_shipped_level_is_harder_than_the_one_before():
    from minotaurus.engine.levels import load_all_levels

    lengths = []
    for level in load_all_levels():
        lengths.append(shortest_path_length(level))
    assert len(lengths) >= 6
    for i in range(1, len(lengths)):
        assert lengths[i] > lengths[i - 1], lengths


def test_impossible_is_the_last_difficulty_and_the_last_level():
    from minotaurus.engine.levels import DIFFICULTY_ORDER, load_all_levels

    assert DIFFICULTY_ORDER["impossible"] == 3
    levels = load_all_levels()
    assert levels[-1].id == "impossible-01"
    assert levels[-1].difficulty == "impossible"
    assert levels[-1].width == 41


def test_test_mazes_are_not_in_the_hand_made_list():
    from minotaurus.engine.levels import load_all_levels, load_portal_levels, load_test_mazes

    hand_made = []
    for level in load_all_levels():
        hand_made.append(level.id)
    tests = load_test_mazes()
    assert len(tests) == 12
    portal = []
    for level in load_portal_levels():
        portal.append(level.id)
    assert sorted(portal) == sorted(hand_made + [level.id for level in tests])
    for level in tests:
        assert level.id not in hand_made


def test_portal_levels_are_hand_made_first_then_test_mazes_each_easy_to_impossible():
    from minotaurus.engine.levels import DIFFICULTY_ORDER, load_portal_levels, load_test_mazes

    test_ids = []
    for level in load_test_mazes():
        test_ids.append(level.id)
    hand_ranks = []
    test_ranks = []
    seen_test = False
    for level in load_portal_levels():
        rank = DIFFICULTY_ORDER[level.difficulty]
        if level.id in test_ids:
            seen_test = True
            test_ranks.append(rank)
        else:
            assert not seen_test, "a hand-made level came after a test maze"
            hand_ranks.append(rank)
    assert hand_ranks == sorted(hand_ranks)
    assert test_ranks == sorted(test_ranks)
    assert hand_ranks[0] == 0 and hand_ranks[-1] == 3
