"""The Pydantic messages are the Python twin of the zod schemas: both check the same samples."""

import json

import pytest
from pydantic import TypeAdapter, ValidationError

from minotaurus.engine.levels import SCHEMA_DIR
from minotaurus.server.messages import (
    BatchResult,
    BrainRecipe,
    BrainResponse,
    LevelInfo,
    RunMessage,
)

SAMPLES = json.loads((SCHEMA_DIR / "message-samples.json").read_text())

ADAPTERS = {
    "run_message": TypeAdapter(RunMessage),
    "levels_response": TypeAdapter(list[LevelInfo]),
    "brain_response": TypeAdapter(BrainResponse),
    "brains_response": TypeAdapter(list[BrainResponse]),
    "brain_recipe": TypeAdapter(BrainRecipe),
    "batch_result": TypeAdapter(BatchResult),
    "batches_response": TypeAdapter(list[BatchResult]),
}


@pytest.mark.parametrize("name", list(ADAPTERS))
def test_valid_samples_accepted(name):
    for sample in SAMPLES[name]["valid"]:
        ADAPTERS[name].validate_python(sample)


@pytest.mark.parametrize("name", list(ADAPTERS))
def test_invalid_samples_rejected(name):
    for sample in SAMPLES[name]["invalid"]:
        with pytest.raises(ValidationError):
            ADAPTERS[name].validate_python(sample)


def test_a_message_dumps_to_the_json_the_page_expects():
    message = ADAPTERS["run_message"].validate_python({"type": "tick", "n": 3, "x": 1, "y": 3})
    assert json.loads(message.model_dump_json()) == {"type": "tick", "n": 3, "x": 1, "y": 3}
