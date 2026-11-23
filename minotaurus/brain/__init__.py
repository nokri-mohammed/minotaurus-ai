"""Brain loading: the safe path from an untrusted .onnx file to a function obs -> action."""

from minotaurus.brain.onnx_brain import Brain, BrainError, load_brain, player

__all__ = ["Brain", "BrainError", "hello", "load_brain", "player"]


def hello() -> str:
    return "brain loader ready"
