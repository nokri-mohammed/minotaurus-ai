"""Export a trained brain to .onnx. Both methods share one input and one output contract."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnx
import torch
from onnx import TensorProto, helper, numpy_helper

from minotaurus.engine.observe import OBS_VERSION, VISITED_COUNTS, VISITED_KEY, obs_size
from minotaurus.trainer.dqn import DQNAgent
from minotaurus.trainer.qtable import N_ACTIONS, QTableAgent, key_weights

OPSET = 17
IR_VERSION = 10
INPUT_NAME = "obs"
OUTPUT_NAME = "scores"


PARAMETERS_KEY = "parameters"  # .onnx metadata: how many numbers the brain stores


def parameter_count(agent: QTableAgent | DQNAgent) -> int:
    """How many numbers the brain stores: the network weights, or 4 scores per table row.

    Example: a DQN with one hidden layer of 16 -> 77*16 + 16 + 16*4 + 4 = 1316.
    """
    if isinstance(agent, DQNAgent):
        total = 0
        for weights in agent.net.parameters():
            total += weights.numel()
        return total
    return len(agent.q) * N_ACTIONS


def _metadata(
    model: onnx.ModelProto,
    name: str,
    method: str,
    level_ids: list[str],
    window: int,
    extra: dict[str, str] | None = None,
    obs_version: int = OBS_VERSION,
):
    meta = {
        "name": name,
        "method": method,
        "obs_version": str(obs_version),
        "window": str(window),
        "memory": "0",
        "levels": json.dumps(level_ids),
        # the visited layer this brain was trained on: visit counts (2026-11-24). Brains without
        # this key were trained on the old yes/no layer; the loader warns about them.
        VISITED_KEY: VISITED_COUNTS,
    }
    if extra is not None:
        meta.update(extra)
    for key, value in meta.items():
        entry = model.metadata_props.add()
        entry.key, entry.value = key, value


def export_dqn(
    agent: DQNAgent,
    path: Path,
    name: str,
    level_ids: list[str],
    window: int = 5,
    extra_meta: dict[str, str] | None = None,
    obs_version: int = OBS_VERSION,
):
    net = agent.net.eval()
    dummy = torch.zeros(1, obs_size(window, obs_version))
    torch.onnx.export(
        net,
        (dummy,),
        str(path),
        input_names=[INPUT_NAME],
        output_names=[OUTPUT_NAME],
        opset_version=OPSET,
        dynamo=False,
    )
    model = onnx.load(str(path))
    model.ir_version = IR_VERSION
    _metadata(model, name, "dqn", level_ids, window, extra_meta, obs_version)
    onnx.save(model, str(path))


def export_qtable(
    agent: QTableAgent,
    path: Path,
    name: str,
    level_ids: list[str],
    window: int = 5,
    extra_meta: dict[str, str] | None = None,
    obs_version: int = OBS_VERSION,
):
    obs_len = obs_size(window, obs_version)
    keys = sorted(agent.q)
    rows = [agent.q[k] for k in keys]
    unknown_row = len(keys)  # a row of zeros for keys the table never saw
    if not keys:
        keys = [0]
        rows = [np.zeros(N_ACTIONS, dtype=np.float32)]
        unknown_row = 1
    table = np.vstack([*rows, np.zeros(N_ACTIONS, dtype=np.float32)]).astype(np.float32)

    init = [
        numpy_helper.from_array(np.array([1.0], dtype=np.float32), "one"),
        numpy_helper.from_array(key_weights(obs_len).astype(np.int64), "key_weights"),
        numpy_helper.from_array(np.array([1], dtype=np.int64), "axes"),
        numpy_helper.from_array(table, "q_rows"),
    ]
    nodes = [
        # min(x, 1) = x - Relu(x - 1): the key reads any visit count as "visited" (as obs_key
        # does). It changes nothing else: walls and exit are 0 or 1, the exit direction -1..1.
        helper.make_node("Sub", [INPUT_NAME, "one"], ["above_one"]),
        helper.make_node("Relu", ["above_one"], ["excess"]),
        helper.make_node("Sub", [INPUT_NAME, "excess"], ["capped"]),
        helper.make_node("Add", ["capped", "one"], ["shifted"]),
        helper.make_node("Cast", ["shifted"], ["as_int"], to=TensorProto.INT64),
        helper.make_node("Mul", ["as_int", "key_weights"], ["weighted"]),
        helper.make_node("ReduceSum", ["weighted", "axes"], ["key"], keepdims=0),
        helper.make_node(
            "LabelEncoder",
            ["key"],
            ["row"],
            domain="ai.onnx.ml",
            keys_int64s=keys,
            values_int64s=list(range(len(keys))),
            default_int64=unknown_row,
        ),
        helper.make_node("Gather", ["q_rows", "row"], [OUTPUT_NAME], axis=0),
    ]
    graph = helper.make_graph(
        nodes,
        "qtable",
        [helper.make_tensor_value_info(INPUT_NAME, TensorProto.FLOAT, [1, obs_len])],
        [helper.make_tensor_value_info(OUTPUT_NAME, TensorProto.FLOAT, [1, N_ACTIONS])],
        init,
    )
    model = helper.make_model(
        graph, opset_imports=[helper.make_opsetid("", OPSET), helper.make_opsetid("ai.onnx.ml", 2)]
    )
    model.ir_version = IR_VERSION
    _metadata(model, name, "qtable", level_ids, window, extra_meta, obs_version)
    onnx.checker.check_model(model)
    onnx.save(model, str(path))
