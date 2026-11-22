"""Training config: Pydantic models are the contract. Wrong settings are named in the message.

`data/schemas/brain-config.schema.json` is generated from these models (editors use it for
completion): `uv run python -m minotaurus.trainer.config`. A test fails if the file drifts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from minotaurus.engine.levels import LEVEL_DIR, SCHEMA_DIR, Level, LevelError, load_level

SCHEMA_FILE = SCHEMA_DIR / "brain-config.schema.json"

Probability = Annotated[float, Field(ge=0, le=1)]
Decay = Annotated[float, Field(gt=0, le=1)]
Positive = Annotated[int, Field(ge=1)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class QTableSettings(_Strict):
    learning_rate: Annotated[float, Field(gt=0, le=1)]
    gamma: Probability
    epsilon_start: Probability
    epsilon_end: Probability
    epsilon_decay: Decay


class DQNSettings(_Strict):
    hidden_layers: Annotated[list[Positive], Field(min_length=1)]
    learning_rate: Annotated[float, Field(gt=0)]
    batch_size: Positive
    gamma: Probability
    replay_size: Positive
    target_update: Positive
    epsilon_start: Probability
    epsilon_end: Probability
    epsilon_decay: Decay
    # Reserved: memory networks are not supported yet, so only 0 (or absent) is accepted.
    memory: Annotated[Literal[0] | None, Field(exclude=True)] = None


class Observation(_Strict):
    window: Literal[5] = 5  # reserved: only 5 is supported yet


class DifficultyLevels(_Strict):
    difficulty: Literal["easy", "medium", "hard"]


class ConfigFile(_Strict):
    name: Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$")]
    method: Literal["qtable", "dqn"]
    levels: Annotated[list[str], Field(min_length=1)] | DifficultyLevels
    episodes: Positive
    seed: int
    observation: Observation = Observation()
    qtable: QTableSettings | None = None
    dqn: DQNSettings | None = None

    @model_validator(mode="after")
    def _method_needs_its_block(self) -> ConfigFile:
        if getattr(self, self.method) is None:
            raise ValueError(f"method '{self.method}' needs a '{self.method}' block")
        return self

    @property
    def window(self) -> int:
        return self.observation.window

    @property
    def params(self) -> dict:
        """The settings of the chosen method, as the agent's keyword arguments."""
        return getattr(self, self.method).model_dump()

    def resolve_levels(self, level_dir: Path = LEVEL_DIR) -> tuple[Level, ...]:
        """The Level objects this config trains on (by id, or all of one difficulty)."""
        all_levels = [load_level(p) for p in sorted(level_dir.glob("*.json"))]
        if isinstance(self.levels, DifficultyLevels):
            levels = tuple(lv for lv in all_levels if lv.difficulty == self.levels.difficulty)
            if not levels:
                raise LevelError(f"no level with difficulty {self.levels.difficulty!r}")
            return levels
        by_id = {lv.id: lv for lv in all_levels}
        for level_id in self.levels:
            if level_id not in by_id:
                raise LevelError(f"no level with id {level_id!r}")
        return tuple(by_id[i] for i in self.levels)


def config_schema() -> dict:
    return ConfigFile.model_json_schema()


def write_schema() -> None:
    SCHEMA_FILE.write_text(json.dumps(config_schema(), indent=2) + "\n")


if __name__ == "__main__":
    write_schema()
    print(f"written: {SCHEMA_FILE}")
