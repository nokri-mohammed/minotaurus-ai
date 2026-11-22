import json

import pytest
from jsonschema import Draft202012Validator

from minotaurus.engine.levels import SCHEMA_DIR

SCHEMA = json.loads((SCHEMA_DIR / "messages.schema.json").read_text())
SAMPLES = json.loads((SCHEMA_DIR / "message-samples.json").read_text())
NAMES = [k for k in SAMPLES if not k.startswith("_")]


def errors(name: str, sample) -> list:
    wrapper = {"$schema": SCHEMA["$schema"], "$defs": SCHEMA["$defs"], "$ref": f"#/$defs/{name}"}
    return list(Draft202012Validator(wrapper).iter_errors(sample))


def test_schema_is_valid():
    Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize("name", NAMES)
def test_valid_samples_accepted(name):
    for sample in SAMPLES[name]["valid"]:
        assert errors(name, sample) == [], sample


@pytest.mark.parametrize("name", NAMES)
def test_invalid_samples_rejected(name):
    for sample in SAMPLES[name]["invalid"]:
        assert errors(name, sample) != [], sample
