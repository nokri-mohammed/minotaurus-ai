"""Training config: load JSON, check it against the schema, name the first wrong setting."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

from minotaurus.engine.levels import LEVEL_DIR, SCHEMA_DIR, Level, LevelError, load_level


class ConfigError(ValueError):
    """The config is wrong. The message names the setting."""


@dataclass(frozen=True)
class TrainConfig:
    raw: dict
    levels: tuple[Level, ...]

    @property
    def name(self) -> str:
        return self.raw["name"]

    @property
    def method(self) -> str:
        return self.raw["method"]

    @property
    def episodes(self) -> int:
        return self.raw["episodes"]

    @property
    def seed(self) -> int:
        return self.raw["seed"]

    @property
    def window(self) -> int:
        return self.raw.get("observation", {}).get("window", 5)

    @property
    def params(self) -> dict:
        return self.raw[self.method]


def _first_error(data: dict) -> str | None:
    schema = json.loads((SCHEMA_DIR / "brain-config.schema.json").read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    if not errors:
        return None
    e = errors[0]
    if e.validator == "required":
        return f"missing setting: {e.message}"
    if e.validator == "additionalProperties":
        return f"unknown setting: {e.message}"
    where = ".".join(str(p) for p in e.path) or "config"
    return f"setting '{where}': {e.message}"


def parse_config(data: dict, level_dir: Path = LEVEL_DIR) -> TrainConfig:
    message = _first_error(data)
    if message:
        raise ConfigError(message)
    all_levels = [load_level(p) for p in sorted(level_dir.glob("*.json"))]
    spec = data["levels"]
    if isinstance(spec, list):
        by_id = {lv.id: lv for lv in all_levels}
        missing = [i for i in spec if i not in by_id]
        if missing:
            raise ConfigError(f"setting 'levels': no level with id {missing[0]!r}")
        levels = tuple(by_id[i] for i in spec)
    else:
        levels = tuple(lv for lv in all_levels if lv.difficulty == spec["difficulty"])
        if not levels:
            raise ConfigError(f"setting 'levels': no level with difficulty {spec['difficulty']!r}")
    return TrainConfig(raw=data, levels=levels)


def load_config(path: str | Path) -> TrainConfig:
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read config {path}: {exc}") from exc
    try:
        return parse_config(data)
    except LevelError as exc:
        raise ConfigError(str(exc)) from exc
