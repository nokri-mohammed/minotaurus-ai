import json

import pytest
from jsonschema import Draft202012Validator

from minotaurus.engine.levels import SCHEMA_DIR

SCHEMA = json.loads((SCHEMA_DIR / "messages.schema.json").read_text())


def check(name: str, sample) -> list:
    wrapper = {"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": f"#/$defs/{name}"}
    return list(Draft202012Validator(wrapper).iter_errors(sample))


def test_schema_is_valid():
    Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize(
    "sample",
    [
        {"type": "run_started", "level_id": "easy-01", "start": {"x": 1, "y": 1}, "step_limit": 52},
        {"type": "tick", "n": 3, "x": 1, "y": 3},
        {"type": "result", "status": "finished", "steps": 13, "seconds": 1.3},
        {"type": "result", "status": "timed_out", "steps": 52, "seconds": 5.2},
        {"type": "error", "message": "bad brain"},
    ],
)
def test_run_messages_accepted(sample):
    assert check("run_message", sample) == []


@pytest.mark.parametrize(
    "sample",
    [
        {"type": "nope"},
        {"type": "tick", "n": "3", "x": 1, "y": 3},
        {"type": "result", "status": "won", "steps": 1, "seconds": 1},
    ],
)
def test_bad_run_messages_rejected(sample):
    assert check("run_message", sample) != []


def test_http_bodies():
    level = {
        "id": "easy-01",
        "name": "First steps",
        "difficulty": "easy",
        "grid": ["#S.E#"],
        "step_limit": 8,
    }
    assert check("levels_response", [level]) == []
    assert check("brain_response", {"name": "q1", "method": "qtable"}) == []
    assert check("brain_response", {"name": "q1", "method": "ppo"}) != []
