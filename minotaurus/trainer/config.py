"""Training config: Pydantic models are the contract. Wrong settings are named in the message.

`data/schemas/brain-config.schema.json` is generated from these models (editors use it for
completion): `uv run python -m minotaurus.trainer.config`. A test fails if the file drifts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from minotaurus.engine.levels import (
    LEVEL_DIR,
    SCHEMA_DIR,
    Level,
    LevelError,
    load_all_levels,
    select_by_difficulty,
    select_by_ids,
)
from minotaurus.engine.pools import Pools, build_pools

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


class GeneratedSettings(_Strict):
    size: Annotated[int, Field(ge=5, le=41)]  # odd: the maze is size x size squares
    maze_seed: int  # fixes the pools, so every training run sees the same mazes
    train: Positive
    validation: Positive
    test: Positive

    @model_validator(mode="after")
    def _size_is_odd(self) -> GeneratedSettings:
        if self.size % 2 == 0:
            raise ValueError("size must be odd")
        return self


class GeneratedLevels(_Strict):
    generated: GeneratedSettings


class ConfigFile(_Strict):
    name: Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$")]
    method: Literal["qtable", "dqn"]
    # Either shape is accepted; Pydantic stores whichever one the JSON matched:
    #   "levels": ["easy-01"]                -> a list of level ids (at least one)
    #   "levels": {"difficulty": "easy"}     -> a DifficultyLevels object (all levels of that difficulty)
    #   "levels": {"generated": {...}}       -> a GeneratedLevels object (made mazes, split in pools)
    levels: Annotated[list[str], Field(min_length=1)] | DifficultyLevels | GeneratedLevels
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

    def pool_settings(self) -> dict | None:
        """The generated-maze settings as a plain dict, or None for hand-made levels."""
        if isinstance(self.levels, GeneratedLevels):
            return self.levels.generated.model_dump()
        return None

    def resolve_pools(self) -> Pools | None:
        """Train, validation and test mazes for "generated" levels; None for any other shape."""
        if not isinstance(self.levels, GeneratedLevels):
            return None
        settings = self.levels.generated
        return build_pools(
            settings.size, settings.maze_seed, settings.train, settings.validation, settings.test
        )

    def resolve_levels(self, level_dir: Path = LEVEL_DIR) -> tuple[Level, ...]:
        """The Level objects this config trains on (by id, or all of one difficulty).

        Returns a tuple of Level objects, in the order the config lists them.

        Example, with "levels": ["easy-01"] in the config file:
            config.resolve_levels()
            # -> (Level(id="easy-01", name="First steps", difficulty="easy", ...),)
            config.resolve_levels()[0].name   # -> "First steps"

        Example, with "levels": {"difficulty": "easy"}: every easy level, as a tuple.
        Raises LevelError when an id, or a difficulty, matches no level file.
        """
        if isinstance(self.levels, GeneratedLevels):  # shape {"generated": {...}}
            pools = self.resolve_pools()
            if pools is None:
                raise LevelError("generated levels have no pools")
            return pools.train
        all_levels = load_all_levels(level_dir)
        if isinstance(self.levels, DifficultyLevels):  # shape {"difficulty": "easy"}
            return select_by_difficulty(all_levels, self.levels.difficulty)
        return select_by_ids(all_levels, self.levels)  # shape ["easy-01", ...]


def config_schema() -> dict:
    return ConfigFile.model_json_schema()


def write_schema() -> None:
    SCHEMA_FILE.write_text(json.dumps(config_schema(), indent=2) + "\n")


if __name__ == "__main__":
    write_schema()
    print(f"written: {SCHEMA_FILE}")
