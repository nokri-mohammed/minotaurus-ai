"""Game engine: the only copy of the rules (levels, observe, MazeEnv, Race)."""

from minotaurus.engine.env import DOWN, LEFT, RIGHT, UP, MazeEnv
from minotaurus.engine.levels import Level, LevelError, load_level, load_level_by_id
from minotaurus.engine.observe import OBS_VERSION, observe
from minotaurus.engine.race import Race, RaceResult

__all__ = [
    "DOWN",
    "LEFT",
    "OBS_VERSION",
    "RIGHT",
    "UP",
    "Level",
    "LevelError",
    "MazeEnv",
    "Race",
    "RaceResult",
    "hello",
    "load_level",
    "load_level_by_id",
    "observe",
]


def hello() -> str:
    return "engine ready"
