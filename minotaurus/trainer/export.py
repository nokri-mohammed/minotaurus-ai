"""Export a trained brain to .onnx. Both methods share one input and one output contract."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnx
import torch
from onnx import TensorProto, helper, numpy_helper

from minotaurus.engine.observe import OBS_VERSION
from minotaurus.trainer.dqn import DQNAgent
from minotaurus.trainer.qtable import KEY_WEIGHTS, N_ACTIONS, OBS_LEN, QTableAgent

OPSET = 17
IR_VERSION = 10
INPUT_NAME = "obs"
OUTPUT_NAME = "scores"


def _metadata(
    model: onnx.ModelProto,
    name: str,
    method: str,
    level_ids: list[str],
    window: int,
    extra: dict[str, str] | None = None,
):
    meta = {
        "name": name,
        "method": method,
        "obs_version": str(OBS_VERSION),
        "window": str(window),
        "memory": "0",
        "levels": json.dumps(level_ids),
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
):
    net = agent.net.eval()
    dummy = torch.zeros(1, OBS_LEN)
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
    _metadata(model, name, "dqn", level_ids, window, extra_meta)
    onnx.save(model, str(path))


def export_qtable(
    agent: QTableAgent,
    path: Path,
    name: str,
    level_ids: list[str],
    window: int = 5,
    extra_meta: dict[str, str] | None = None,
):
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
        numpy_helper.from_array(KEY_WEIGHTS.astype(np.int64), "key_weights"),
        numpy_helper.from_array(np.array([1], dtype=np.int64), "axes"),
        numpy_helper.from_array(table, "q_rows"),
    ]
    nodes = [
        helper.make_node("Add", [INPUT_NAME, "one"], ["shifted"]),
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
        [helper.make_tensor_value_info(INPUT_NAME, TensorProto.FLOAT, [1, OBS_LEN])],
        [helper.make_tensor_value_info(OUTPUT_NAME, TensorProto.FLOAT, [1, N_ACTIONS])],
        init,
    )
    model = helper.make_model(
        graph, opset_imports=[helper.make_opsetid("", OPSET), helper.make_opsetid("ai.onnx.ml", 2)]
    )
    model.ir_version = IR_VERSION
    _metadata(model, name, "qtable", level_ids, window, extra_meta)
    onnx.checker.check_model(model)
    onnx.save(model, str(path))
