"""Training config: Pydantic models are the contract. Wrong settings are named in the message.

`data/schemas/brain-config.schema.json` is generated from these models (editors use it for
completion): `uv run python -m minotaurus.trainer.config`. A test fails if the file drifts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from minotaurus.engine.levels import LEVEL_DIR, SCHEMA_DIR, Level, LevelError, load_level

SCHEMA_FILE = SCHEMA_DIR / "brain-config.schema.json"

Probability = Annotated[float, Field(ge=0, le=1)]
Decay = Annotated[float, Field(gt=0, le=1)]
Positive = Annotated[int, Field(ge=1)]


class ConfigError(ValueError):
    """The config is wrong. The message names the setting."""


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


def config_schema() -> dict:
    return ConfigFile.model_json_schema()


def write_schema() -> None:
    SCHEMA_FILE.write_text(json.dumps(config_schema(), indent=2) + "\n")


@dataclass(frozen=True)
class TrainConfig:
    """A checked config plus its resolved levels. The trainer reads only this."""

    file: ConfigFile
    raw: dict  # what the user wrote, saved as config.json in the run folder
    levels: tuple[Level, ...]

    @property
    def name(self) -> str:
        return self.file.name

    @property
    def method(self) -> str:
        return self.file.method

    @property
    def episodes(self) -> int:
        return self.file.episodes

    @property
    def seed(self) -> int:
        return self.file.seed

    @property
    def window(self) -> int:
        return self.file.observation.window

    @property
    def params(self) -> dict:
        return getattr(self.file, self.method).model_dump()


_UNION_BRANCHES = {"list[str]", "DifficultyLevels"}


def _message(error: ValidationError) -> str:
    first = error.errors()[0]
    where = ".".join(str(p) for p in first["loc"] if p not in _UNION_BRANCHES)
    if first["type"] == "missing":
        return f"missing setting: {where}"
    if first["type"] == "extra_forbidden":
        return f"unknown setting: {where}"
    text = first["msg"].removeprefix("Value error, ")
    return f"setting '{where or 'config'}': {text}"


def parse_config(data: dict, level_dir: Path = LEVEL_DIR) -> TrainConfig:
    try:
        file = ConfigFile.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(_message(exc)) from exc
    all_levels = [load_level(p) for p in sorted(level_dir.glob("*.json"))]
    spec = file.levels
    if isinstance(spec, list):
        by_id = {lv.id: lv for lv in all_levels}
        missing = [i for i in spec if i not in by_id]
        if missing:
            raise ConfigError(f"setting 'levels': no level with id {missing[0]!r}")
        levels = tuple(by_id[i] for i in spec)
    else:
        levels = tuple(lv for lv in all_levels if lv.difficulty == spec.difficulty)
        if not levels:
            raise ConfigError(f"setting 'levels': no level with difficulty {spec.difficulty!r}")
    return TrainConfig(file=file, raw=data, levels=levels)


def load_config(path: str | Path) -> TrainConfig:
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read config {path}: {exc}") from exc
    try:
        return parse_config(data)
    except LevelError as exc:
        raise ConfigError(str(exc)) from exc


if __name__ == "__main__":
    write_schema()
    print(f"written: {SCHEMA_FILE}")
