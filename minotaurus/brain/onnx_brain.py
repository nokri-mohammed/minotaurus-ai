"""Safe loader for untrusted .onnx brains. Returns a plain callable: obs -> action.

Checks, in order: file size, onnx checker, operator allowlist, input and output shape, metadata
(obs_version), and a per-step time limit measured on a test run (after one untimed warm-up call)
and on every later call.
"""

from __future__ import annotations

import hashlib
import math
import random
import time
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort

from minotaurus.engine.observe import OBS_VERSION, VISITED_COUNTS, VISITED_KEY

MAX_BYTES = 1_000_000  # 1 MB
TIME_LIMIT_S = 0.05  # per step
POLICY_EPSILON_KEY = "policy_epsilon"  # metadata: share of random moves when playing
OBS_LEN = 77
N_ACTIONS = 4
ALLOWED_OPS = frozenset(
    {
        "Gemm",
        "MatMul",
        "Add",
        "Sub",
        "Mul",
        "Relu",
        "Tanh",
        "Sigmoid",
        "Cast",
        "ReduceSum",
        "Gather",
        "Reshape",
        "Flatten",
        "Squeeze",
        "Unsqueeze",
        "Identity",
        "Constant",
        "LabelEncoder",
    }
)
ALLOWED_DOMAINS = frozenset({"", "ai.onnx", "ai.onnx.ml"})


class BrainError(ValueError):
    """The brain file is not acceptable. The message says why."""


class BrainWarning(UserWarning):
    """The brain is accepted, but may not play as it was trained. The message says why."""


OLD_VISITED_WARNING = (
    'this brain was trained with the yes/no visited input (no visited="counts" metadata): '
    "it now sees visit counts, which differ only on squares visited more than once (a bump "
    "counts too), so it may play differently where it walks back over its own path"
)


@dataclass
class Brain:
    session: ort.InferenceSession = field(repr=False)
    meta: dict[str, str]
    time_limit_s: float = TIME_LIMIT_S
    # Share of moves made at random when playing (metadata "policy_epsilon"); 0 = always the best
    # move. Applied by player(), never by __call__.
    policy_epsilon: float = 0.0
    digest: str = ""  # SHA-256 of the file: with the level id it seeds the random moves of a run

    @property
    def visited_counts(self) -> bool:
        """True when the brain was trained on the visit-count layer (metadata visited="counts")."""
        return self.meta.get(VISITED_KEY) == VISITED_COUNTS

    @property
    def name(self) -> str:
        return self.meta.get("name", "")

    @property
    def method(self) -> str:
        return self.meta.get("method", "")

    def scores(self, obs: np.ndarray) -> np.ndarray:
        x = np.asarray(obs, dtype=np.float32).reshape(1, OBS_LEN)
        start = time.perf_counter()
        out = self.session.run(None, {self.session.get_inputs()[0].name: x})[0]
        if time.perf_counter() - start > self.time_limit_s:
            raise BrainError(f"brain is too slow: a step took more than {self.time_limit_s} s")
        return np.asarray(out, dtype=np.float32).reshape(N_ACTIONS)

    def __call__(self, obs: np.ndarray) -> int:
        return int(np.argmax(self.scores(obs)))


def _policy_epsilon(meta: dict[str, str]) -> float:
    """The brain's random-move rate from its metadata: 0 when absent, else a number 0 to 1."""
    text = meta.get(POLICY_EPSILON_KEY)
    if text is None:
        return 0.0
    try:
        value = float(text)
    except ValueError:
        value = float("nan")
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise BrainError(f"bad policy_epsilon {text!r}: must be a number from 0 to 1")
    return value


def player(brain: Callable[[np.ndarray], int], seed: str, epsilon: float | None = None):
    """The brain as it plays: a random move with probability epsilon, else its best move.

    epsilon defaults to the brain's own policy_epsilon (0 for a plain function or a brain without
    the setting). With 0 the brain itself is returned, unchanged. The random moves come from
    random.Random(seed), so the same seed replays the same run.
    Example: player(brain, seed=f"{brain.digest}|easy-01").
    """
    if epsilon is None:
        epsilon = getattr(brain, "policy_epsilon", 0.0)
    if epsilon == 0.0:
        return brain
    rng = random.Random(seed)

    def play(obs: np.ndarray) -> int:
        if rng.random() < epsilon:
            return rng.randrange(N_ACTIONS)
        return brain(obs)

    return play


def _dims(value_info: onnx.ValueInfoProto) -> list[int | None]:
    dims = value_info.type.tensor_type.shape.dim
    return [d.dim_value if d.HasField("dim_value") else None for d in dims]


def load_brain(
    path: str | Path, *, max_bytes: int = MAX_BYTES, time_limit_s: float = TIME_LIMIT_S
) -> Brain:
    path = Path(path)
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise BrainError(f"cannot read {path}: {exc}") from exc
    if size > max_bytes:
        raise BrainError(f"file is too big: {size} bytes, the limit is {max_bytes}")
    try:
        model = onnx.load(str(path), load_external_data=False)
        onnx.checker.check_model(model)
    except Exception as exc:
        raise BrainError(f"not a valid ONNX file: {exc}") from exc
    if any(init.external_data for init in model.graph.initializer):
        raise BrainError("external data files are not allowed")
    for opset in model.opset_import:
        if opset.domain not in ALLOWED_DOMAINS:
            raise BrainError(f"forbidden operator domain: {opset.domain!r}")
    for node in model.graph.node:
        if node.domain not in ALLOWED_DOMAINS or node.op_type not in ALLOWED_OPS:
            raise BrainError(f"forbidden operator: {node.op_type}")
    if len(model.graph.input) != 1 or _dims(model.graph.input[0]) != [1, OBS_LEN]:
        raise BrainError(f"wrong input: expected one input of shape [1, {OBS_LEN}]")
    if len(model.graph.output) != 1 or _dims(model.graph.output[0])[-1] != N_ACTIONS:
        raise BrainError(f"wrong output: expected {N_ACTIONS} scores")
    meta = {p.key: p.value for p in model.metadata_props}
    policy_epsilon = _policy_epsilon(meta)
    if meta.get("obs_version") != str(OBS_VERSION):
        raise BrainError(
            f"wrong obs_version: file has {meta.get('obs_version')!r}, this game uses {OBS_VERSION}"
        )
    try:
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.log_severity_level = 4
        session = ort.InferenceSession(
            model.SerializeToString(), options, providers=["CPUExecutionProvider"]
        )
    except Exception as exc:
        raise BrainError(f"cannot load the model: {exc}") from exc
    brain = Brain(
        session=session,
        meta=meta,
        time_limit_s=time_limit_s,
        policy_epsilon=policy_epsilon,
        digest=hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    try:
        # Untimed warm-up: the first run of a new session can be slow (a cold start), which is
        # not the brain's fault. The test run below and every later step are timed as before.
        session.run(None, {session.get_inputs()[0].name: np.zeros((1, OBS_LEN), np.float32)})
        out = brain.scores(np.zeros(OBS_LEN, dtype=np.float32))
    except BrainError:
        raise
    except Exception as exc:
        raise BrainError(f"test run failed: {exc}") from exc
    if not np.all(np.isfinite(out)):
        raise BrainError("test run gave scores that are not numbers")
    if not brain.visited_counts:
        # accepted (a warning, not an error): old brains see the same input until a revisit
        warnings.warn(OLD_VISITED_WARNING, BrainWarning, stacklevel=2)
    return brain
