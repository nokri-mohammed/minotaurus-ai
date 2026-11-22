"""Safe loader for untrusted .onnx brains. Returns a plain callable: obs -> action.

Checks, in order: file size, onnx checker, operator allowlist, input and output shape, metadata
(obs_version), and a per-step time limit that is measured on a test run and on every later call.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort

from minotaurus.engine.observe import OBS_VERSION

MAX_BYTES = 1_000_000  # 1 MB
TIME_LIMIT_S = 0.05  # per step
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


@dataclass
class Brain:
    session: ort.InferenceSession = field(repr=False)
    meta: dict[str, str]
    time_limit_s: float = TIME_LIMIT_S

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
    brain = Brain(session=session, meta=meta, time_limit_s=time_limit_s)
    try:
        out = brain.scores(np.zeros(OBS_LEN, dtype=np.float32))
    except BrainError:
        raise
    except Exception as exc:
        raise BrainError(f"test run failed: {exc}") from exc
    if not np.all(np.isfinite(out)):
        raise BrainError("test run gave scores that are not numbers")
    return brain
