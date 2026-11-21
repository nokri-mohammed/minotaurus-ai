import json

import pytest
from jsonschema import Draft202012Validator

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


def test_brain_config_schema_is_valid_and_checks_samples():
    from minotaurus.engine.levels import SCHEMA_DIR

    schema = json.loads((SCHEMA_DIR / "brain-config.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    v = Draft202012Validator(schema)
    good = {
        "name": "q1",
        "method": "qtable",
        "levels": ["easy-01"],
        "episodes": 100,
        "seed": 1,
        "qtable": {
            "learning_rate": 0.1,
            "gamma": 0.95,
            "epsilon_start": 1.0,
            "epsilon_end": 0.05,
            "epsilon_decay": 0.999,
        },
    }
    assert not list(v.iter_errors(good))
    assert list(v.iter_errors({**good, "method": "ppo"}))
    assert list(v.iter_errors({**good, "episodes": 0}))
    assert list(v.iter_errors({**good, "observation": {"window": 7}}))  # reserved
    no_block = {k: val for k, val in good.items() if k != "qtable"}
    assert list(v.iter_errors(no_block))  # method qtable needs its block
