import json
from pathlib import Path

import numpy as np
import onnx
import pytest
import torch
from onnx import TensorProto, helper, numpy_helper
from pydantic import ValidationError

from minotaurus.brain import BrainError, load_brain
from minotaurus.engine import RIGHT, MazeEnv, load_level_by_id
from minotaurus.engine.levels import LevelError
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.dqn import DQNAgent
from minotaurus.trainer.export import export_dqn, export_qtable
from minotaurus.trainer.qtable import QTableAgent, obs_key
from minotaurus.trainer.train import train
from tests.conftest import make_level

EXAMPLES = Path(__file__).resolve().parents[1] / "data" / "examples"


def small_qtable_config(episodes: int = 30) -> dict:
    cfg = json.loads((EXAMPLES / "qtable-brain.json").read_text())
    cfg["episodes"] = episodes
    return cfg


def small_dqn_config(episodes: int = 8) -> dict:
    cfg = json.loads((EXAMPLES / "dqn-brain.json").read_text())
    cfg["episodes"] = episodes
    cfg["dqn"]["hidden_layers"] = [16]
    cfg["dqn"]["batch_size"] = 8
    return cfg


# ---- config ----


@pytest.mark.parametrize("name", ["qtable-brain.json", "dqn-brain.json"])
def test_examples_validate(name):
    cfg = ConfigFile.model_validate_json((EXAMPLES / name).read_text())
    assert cfg.resolve_levels()[0].id == "easy-01"


def test_config_error_names_the_setting():
    data = small_qtable_config()
    data["qtable"]["learning_rate"] = 5
    with pytest.raises(ValidationError, match="qtable.learning_rate"):
        ConfigFile.model_validate(data)


def test_config_missing_and_unknown_settings():
    data = small_qtable_config()
    del data["episodes"]
    with pytest.raises(ValidationError, match="episodes"):
        ConfigFile.model_validate(data)
    data = small_qtable_config()
    data["bogus"] = 1
    with pytest.raises(ValidationError, match="bogus"):
        ConfigFile.model_validate(data)


def test_config_unknown_level():
    data = small_qtable_config()
    data["levels"] = ["nope-99"]
    with pytest.raises(LevelError, match="nope-99"):
        ConfigFile.model_validate(data).resolve_levels()


def test_config_difficulty_selects_levels():
    data = small_qtable_config()
    data["levels"] = {"difficulty": "easy"}
    assert [lv.id for lv in ConfigFile.model_validate(data).resolve_levels()] == ["easy-01"]


def test_config_schema_file_is_generated_from_the_models():
    import json

    from minotaurus.engine.levels import SCHEMA_DIR
    from minotaurus.trainer.config import config_schema

    on_disk = json.loads((SCHEMA_DIR / "brain-config.schema.json").read_text())
    assert on_disk == config_schema(), "run: uv run python -m minotaurus.trainer.config"


def test_config_reserved_settings_are_rejected():
    data = small_qtable_config()
    data["observation"] = {"window": 7}
    with pytest.raises(ValidationError, match="observation.window"):
        ConfigFile.model_validate(data)
    data = small_dqn_config()
    data["dqn"]["memory"] = 1
    with pytest.raises(ValidationError, match="dqn.memory"):
        ConfigFile.model_validate(data)


def test_config_method_needs_its_own_block():
    data = small_qtable_config()
    del data["qtable"]
    with pytest.raises(ValidationError, match="qtable"):
        ConfigFile.model_validate(data)


def test_config_bad_method_and_episodes():
    data = small_qtable_config()
    data["method"] = "ppo"
    with pytest.raises(ValidationError, match="method"):
        ConfigFile.model_validate(data)
    data = small_qtable_config()
    data["episodes"] = 0
    with pytest.raises(ValidationError, match="episodes"):
        ConfigFile.model_validate(data)


def test_config_params_are_the_agent_arguments():
    cfg = ConfigFile.model_validate(small_dqn_config())
    assert "memory" not in cfg.params and "hidden_layers" in cfg.params
    assert cfg.window == 5


# ---- q-table ----


def test_qtable_learns_corridor_goes_right():
    level = make_level(["#######", "#S...E#", "#######"])
    env = MazeEnv(level)
    agent = QTableAgent(0.5, 0.9, 1.0, 0.05, 0.9, seed=0)
    for _ in range(40):
        obs, _ = env.reset()
        done = False
        while not done:
            a = agent.act(obs)
            nxt, r, term, trunc, _ = env.step(a)
            agent.update(obs, a, r, nxt, term)
            obs, done = nxt, term or trunc
        agent.end_episode()
    obs, _ = env.reset()
    assert agent.act(obs, explore=False) == RIGHT


def test_obs_key_differs_and_is_stable():
    level = load_level_by_id("easy-01")
    env = MazeEnv(level)
    a, _ = env.reset()
    b, *_ = env.step(RIGHT)
    assert obs_key(a) == obs_key(a.copy())
    assert obs_key(a) != obs_key(b)


# ---- dqn ----


def test_dqn_loss_drops_and_weights_change():
    agent = DQNAgent([16], 0.01, 8, 0.9, 100, 10, 1.0, 0.05, 0.9, seed=0)
    rng = np.random.default_rng(0)
    batch = [
        (
            rng.random(77, dtype=np.float32),
            int(rng.integers(4)),
            float(rng.random()),
            rng.random(77, dtype=np.float32),
            False,
        )
        for _ in range(8)
    ]
    before = [p.detach().clone() for p in agent.net.parameters()]
    first = agent.learn(batch)
    assert any(not torch.equal(b, p) for b, p in zip(before, agent.net.parameters(), strict=True))
    for _ in range(60):
        last = agent.learn(batch)
    assert last < first


# ---- training loop ----


def test_train_is_seeded(tmp_path):
    cfg = ConfigFile.model_validate(small_qtable_config(40))
    a = train(cfg, run_dir=tmp_path / "a", log_every=5)
    b = train(cfg, run_dir=tmp_path / "b", log_every=5)
    assert (a / "metrics.jsonl").read_text() == (b / "metrics.jsonl").read_text()
    lines = (a / "metrics.jsonl").read_text().splitlines()
    assert len(lines) == 8
    assert set(json.loads(lines[0])) >= {
        "episode",
        "avg_reward",
        "avg_steps",
        "success_rate",
        "epsilon",
        "loss",
    }
    assert (a / "config.json").exists() and (a / "brain.onnx").exists()


def test_train_dqn_runs_and_exports(tmp_path):
    cfg = ConfigFile.model_validate(small_dqn_config())
    run = train(cfg, run_dir=tmp_path / "d", log_every=4)
    assert load_brain(run / "brain.onnx").method == "dqn"


# ---- export: ONNX output equals the in-memory brain ----


def sample_observations(n: int = 60):
    env = MazeEnv(load_level_by_id("easy-01"))
    rng = np.random.default_rng(3)
    obs, _ = env.reset()
    seen = [obs]
    for _ in range(n):
        obs, _, term, trunc, _ = env.step(int(rng.integers(4)))
        seen.append(obs)
        if term or trunc:
            obs, _ = env.reset()
    return seen


def test_qtable_onnx_equals_memory(tmp_path):
    cfg = ConfigFile.model_validate(small_qtable_config(60))
    agent = QTableAgent(**cfg.params, seed=1)
    env = MazeEnv(cfg.resolve_levels()[0])
    for _ in range(60):
        obs, _ = env.reset()
        done = False
        while not done:
            a = agent.act(obs)
            nxt, r, term, trunc, _ = env.step(a)
            agent.update(obs, a, r, nxt, term)
            obs, done = nxt, term or trunc
    export_qtable(agent, tmp_path / "q.onnx", "q", ["easy-01"])
    brain = load_brain(tmp_path / "q.onnx")
    observations = sample_observations()
    assert any(obs_key(o) in agent.q for o in observations)
    for obs in observations:
        np.testing.assert_array_equal(brain.scores(obs), agent.scores(obs))
    # an observation the table never saw gives zeros
    unseen = np.ones(77, dtype=np.float32)
    assert obs_key(unseen) not in agent.q
    np.testing.assert_array_equal(brain.scores(unseen), np.zeros(4, dtype=np.float32))


def test_dqn_onnx_equals_memory(tmp_path):
    agent = DQNAgent([16, 8], 0.01, 8, 0.9, 100, 10, 1.0, 0.05, 0.9, seed=2)
    export_dqn(agent, tmp_path / "d.onnx", "d", ["easy-01"])
    brain = load_brain(tmp_path / "d.onnx")
    for obs in sample_observations():
        np.testing.assert_allclose(brain.scores(obs), agent.scores(obs), atol=1e-5)
        assert brain(obs) == int(np.argmax(agent.scores(obs)))


def test_exported_metadata(tmp_path):
    agent = QTableAgent(0.1, 0.9, 1.0, 0.1, 0.9)
    export_qtable(agent, tmp_path / "q.onnx", "mybrain", ["easy-01"])
    brain = load_brain(tmp_path / "q.onnx")
    assert brain.name == "mybrain" and brain.method == "qtable"
    assert brain.meta["obs_version"] == "1" and brain.meta["window"] == "5"
    assert brain.meta["memory"] == "0" and json.loads(brain.meta["levels"]) == ["easy-01"]


# ---- loader rejects bad brains ----


def make_model(tmp_path, *, op="Relu", in_shape=(1, 77), version="1", name="m.onnx"):
    weights = numpy_helper.from_array(np.ones((in_shape[1], 4), dtype=np.float32), "w")
    graph = helper.make_graph(
        [helper.make_node("MatMul", ["x", "w"], ["y"]), helper.make_node(op, ["y"], ["z"])],
        "g",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, list(in_shape))],
        [helper.make_tensor_value_info("z", TensorProto.FLOAT, [1, 4])],
        [weights],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 10
    entry = model.metadata_props.add()
    entry.key, entry.value = "obs_version", version
    path = tmp_path / name
    onnx.save(model, str(path))
    return path


def test_loader_rejects_oversize(tmp_path):
    path = tmp_path / "big.onnx"
    path.write_bytes(b"0" * 1_000_001)
    with pytest.raises(BrainError, match="too big"):
        load_brain(path)


def test_loader_rejects_garbage(tmp_path):
    path = tmp_path / "junk.onnx"
    path.write_bytes(b"not a model")
    with pytest.raises(BrainError):
        load_brain(path)


def test_loader_rejects_wrong_shape(tmp_path):
    with pytest.raises(BrainError, match="input"):
        load_brain(make_model(tmp_path, in_shape=(1, 10)))


def test_loader_rejects_forbidden_operator(tmp_path):
    with pytest.raises(BrainError, match="forbidden operator: Exp"):
        load_brain(make_model(tmp_path, op="Exp"))


def test_loader_rejects_wrong_obs_version(tmp_path):
    with pytest.raises(BrainError, match="obs_version"):
        load_brain(make_model(tmp_path, version="2"))


def test_loader_rejects_slow_model(tmp_path):
    agent = DQNAgent([64], 0.01, 8, 0.9, 100, 10, 1.0, 0.05, 0.9)
    export_dqn(agent, tmp_path / "s.onnx", "s", ["easy-01"])
    with pytest.raises(BrainError, match="too slow"):
        load_brain(tmp_path / "s.onnx", time_limit_s=1e-9)


def test_loader_accepts_valid_model(tmp_path):
    brain = load_brain(make_model(tmp_path, op="Relu"), max_bytes=10_000)
    assert brain(np.zeros(77, dtype=np.float32)) in range(4)
