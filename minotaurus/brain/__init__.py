"""Brain loading: the safe path from an untrusted .onnx file to a function obs -> action."""

from minotaurus.brain.onnx_brain import (
    Brain,
    BrainError,
    BrainWarning,
    load_brain,
    obs_version_of,
    player,
)

__all__ = ["Brain", "BrainError", "BrainWarning", "hello", "load_brain", "obs_version_of", "player"]


def hello() -> str:
    return "brain loader ready"
