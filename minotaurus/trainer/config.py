"""Training config: Pydantic models are the contract. Wrong settings are named in the message.

`data/schemas/brain-config.schema.json` is generated from these models (editors use it for
completion): `uv run python -m minotaurus.trainer.config`. A test fails if the file drifts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from minotaurus.engine.generate import MAX_SIZE as MAX_MAZE_SIZE
from minotaurus.engine.generate import MIN_SIZE as MIN_MAZE_SIZE
from minotaurus.engine.levels import (
    LEVEL_DIR,
    SCHEMA_DIR,
    Level,
    LevelError,
    load_all_levels,
    select_by_difficulty,
    select_by_ids,
)
from minotaurus.engine.pools import Pools, build_pools, practice_mazes

SCHEMA_FILE = SCHEMA_DIR / "brain-config.schema.json"
DEFAULT_EVAL_EVERY = 250  # tries between validation checks when the config has pools

Probability = Annotated[float, Field(ge=0, le=1)]
Decay = Annotated[float, Field(gt=0, le=1)]
Positive = Annotated[int, Field(ge=1)]
NonNegative = Annotated[float, Field(ge=0)]


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
    # Training only, off by default: add gamma * phi(s') - phi(s) to each reward, where phi is
    # minus the walking distance to the exit (see trainer/shaping.py).
    shaping: bool = False
    # With shaping on, False keeps the plain reward on a bump into a wall (experimental).
    shaping_on_bump: bool = True
    # Training only, off by default (0): rewards from the visit count of the square the dot
    # ends on, counted before the step (a bump re-enters its own square). novelty_bonus is added
    # for a square never visited; revisit_penalty is taken off once for every earlier visit.
    novelty_bonus: NonNegative = 0.0
    revisit_penalty: NonNegative = 0.0


# DQN settings read by the training loop, not by the agent.
TRAINING_LOOP_SETTINGS = frozenset(
    {"shaping", "shaping_on_bump", "novelty_bonus", "revisit_penalty"}
)


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
    # Off by default: a start square picked by each maze's seed instead of the top left, and the
    # exit as a gap in the outer wall (like the hand-made levels) instead of inside the maze.
    # The walls stay the same, so the three pools hold the same mazes.
    random_start: bool = False
    border_exit: bool = False
    # Optional mixed sizes, e.g. [9, 11, 13, 17, 21]: every pool is split evenly over these sizes,
    # so the brain sees all of them. `size` must be one of them. Off (None) = only `size`.
    sizes: Annotated[list[int], Field(min_length=2)] | None = None

    @model_validator(mode="after")
    def _sizes_are_valid(self) -> GeneratedSettings:
        if self.sizes is None:
            return self
        for size in self.sizes:
            if size % 2 == 0 or size < MIN_MAZE_SIZE or size > MAX_MAZE_SIZE:
                raise ValueError(
                    f"sizes: {size} must be odd, from {MIN_MAZE_SIZE} to {MAX_MAZE_SIZE}"
                )
        if len(set(self.sizes)) != len(self.sizes):
            raise ValueError("sizes must all be different")
        if self.size not in self.sizes:
            raise ValueError("sizes must include size")
        return self

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
    # Step limit for training episodes, as a multiple of the shortest path. None keeps each level's
    # own factor (4). Scoring and the arena always use the level's own factor.
    train_step_limit_factor: Annotated[float, Field(gt=0)] | None = None
    # Experimental size curriculum, generated levels only: maze sizes in order, the last one the
    # pool size, e.g. [5, 7, 9]. The episodes are split evenly over the stages. It did not help in
    # the 2026-11-23 research (docs/research/2026-11-23-dqn-shaping.md).
    stages: list[int] | None = None
    # Best brain on validation (G4), generated levels only: check the brain on the validation
    # mazes every `eval_every` tries and at the end, and export the best one. Unset means
    # DEFAULT_EVAL_EVERY when there are pools; 0 switches it off (the last brain is exported).
    eval_every: Annotated[int, Field(ge=0)] | None = None
    # Share of moves the exported brain makes at random when it plays (arena and scoring), written
    # into the .onnx as "policy_epsilon". 0 (the default) writes nothing: the brain plays as before.
    policy_epsilon: Probability = 0.0
    # Never pick a move into a wall the dot can see (training and play, off by default): random
    # moves, best moves and the learning target use only the free moves. Written into the .onnx
    # as "wall_mask", so the arena and scoring apply it to this brain.
    wall_mask: bool = False
    # Early stop, off by default: stop training after this many validation checks in a row
    # without a better validation score (a tie is not better), then export the best brain as
    # usual. Needs validation checks (generated levels, eval_every not 0).
    patience: Positive | None = None
    # Several seeds in one go (optional): one run per seed, e.g. [1, 2, 3, 4]. None trains the
    # single `seed`. The command line option --seeds N overrides it.
    seeds: Annotated[list[int], Field(min_length=1)] | None = None
    # How many runs go at the same time (optional). None means one per CPU core, at most one per
    # seed. The command line option --parallel overrides it.
    parallel: Positive | None = None

    @model_validator(mode="after")
    def _seeds_are_different(self) -> ConfigFile:
        if self.seeds is not None and len(set(self.seeds)) != len(self.seeds):
            raise ValueError("seeds must all be different")
        return self

    @model_validator(mode="after")
    def _method_needs_its_block(self) -> ConfigFile:
        if getattr(self, self.method) is None:
            raise ValueError(f"method '{self.method}' needs a '{self.method}' block")
        return self

    @model_validator(mode="after")
    def _eval_every_needs_pools(self) -> ConfigFile:
        if self.eval_every and not isinstance(self.levels, GeneratedLevels):
            raise ValueError("eval_every needs generated levels (validation mazes)")
        return self

    @model_validator(mode="after")
    def _patience_needs_checks(self) -> ConfigFile:
        if self.patience is None:
            return self
        if not isinstance(self.levels, GeneratedLevels):
            raise ValueError("patience needs generated levels (validation mazes)")  # noqa: TRY004
        if self.eval_every == 0:
            raise ValueError("patience needs validation checks: eval_every must not be 0")
        return self

    @model_validator(mode="after")
    def _stages_fit_the_pools(self) -> ConfigFile:
        if self.stages is None:
            return self
        if not isinstance(self.levels, GeneratedLevels):
            raise ValueError("stages need generated levels")  # noqa: TRY004  Pydantic wants ValueError
        if len(self.stages) < 2:
            raise ValueError("stages need at least two sizes")
        for size in self.stages:
            if size % 2 == 0 or size < MIN_MAZE_SIZE or size > MAX_MAZE_SIZE:
                raise ValueError(
                    f"stages: size {size} must be odd, from {MIN_MAZE_SIZE} to {MAX_MAZE_SIZE}"
                )
        if self.levels.generated.sizes is not None:
            raise ValueError("stages cannot be used together with sizes")
        if self.stages[-1] != self.levels.generated.size:
            raise ValueError("stages: the last size must be the generated size")
        return self

    @property
    def window(self) -> int:
        return self.observation.window

    @property
    def params(self) -> dict:
        """The settings of the chosen method, as the agent's keyword arguments."""
        return getattr(self, self.method).model_dump(exclude=set(TRAINING_LOOP_SETTINGS))

    @property
    def shaping(self) -> bool:
        """True when the training rewards get potential-based shaping (DQN only)."""
        return self.dqn is not None and self.method == "dqn" and self.dqn.shaping

    def for_seed(self, seed: int) -> ConfigFile:
        """The same recipe for one seed: `seed` set, `seeds` and `parallel` left out.

        Example: a config with seeds [4, 5] -> for_seed(5) trains one run with seed 5.
        """
        data = json.loads(self.model_dump_json(exclude_unset=True))
        data["seed"] = seed
        data.pop("seeds", None)
        data.pop("parallel", None)
        return ConfigFile.model_validate(data)

    def pool_settings(self) -> dict | None:
        """The generated-maze settings as a plain dict, or None for hand-made levels.

        random_start and border_exit are left out while they are off, so the dict is the same as
        for brains exported before they existed (scoring compares it with the brain's metadata).
        """
        if isinstance(self.levels, GeneratedLevels):
            return self.levels.generated.model_dump(exclude_defaults=True)
        return None

    def resolve_pools(self) -> Pools | None:
        """Train, validation and test mazes for "generated" levels; None for any other shape."""
        if not isinstance(self.levels, GeneratedLevels):
            return None
        settings = self.levels.generated
        sizes = None
        if settings.sizes is not None:
            sizes = tuple(settings.sizes)
        return build_pools(
            settings.size,
            settings.maze_seed,
            settings.train,
            settings.validation,
            settings.test,
            random_start=settings.random_start,
            border_exit=settings.border_exit,
            sizes=sizes,
        )

    def validation_interval(self, pools: Pools | None) -> int:
        """Tries between validation checks for the best-brain export; 0 means no checks.

        Example: generated levels and no "eval_every" -> 250; hand-made levels -> 0.
        """
        if pools is None:
            return 0
        if self.eval_every is None:
            return DEFAULT_EVAL_EVERY
        return self.eval_every

    def training_options(self, pools: Pools | None) -> dict:
        """Every training option as this run uses it (effective values, not just what was set).

        Example, a plain Q-table run: {"shaping": False, "shaping_on_bump": None,
        "train_step_limit_factor": None, "stages": None, "eval_every": 0, "policy_epsilon": 0.0}.
        """
        on_bump = None
        novelty_bonus = None
        revisit_penalty = None
        if self.method == "dqn":
            on_bump = self.dqn.shaping_on_bump
            novelty_bonus = self.dqn.novelty_bonus
            revisit_penalty = self.dqn.revisit_penalty
        return {
            "shaping": self.shaping,
            "shaping_on_bump": on_bump,
            "novelty_bonus": novelty_bonus,
            "revisit_penalty": revisit_penalty,
            "train_step_limit_factor": self.train_step_limit_factor,
            "stages": self.stages,
            "eval_every": self.validation_interval(pools),
            "policy_epsilon": self.policy_epsilon,
            "wall_mask": self.wall_mask,
            "patience": self.patience,
        }

    def resolve_stages(self, pools: Pools | None) -> list[tuple[Level, ...]] | None:
        """The levels of each curriculum stage, or None without stages.

        Every stage but the last is up to `train` practice mazes of that size (fewer when the
        size has fewer); the last stage is the train pool, so validation and test stay as they are.
        """
        if self.stages is None or pools is None:
            return None
        settings = self.levels.generated
        result = []
        for size in self.stages[:-1]:
            result.append(
                practice_mazes(
                    size,
                    settings.maze_seed,
                    settings.train,
                    random_start=settings.random_start,
                    border_exit=settings.border_exit,
                )
            )
        result.append(pools.train)
        return result

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
