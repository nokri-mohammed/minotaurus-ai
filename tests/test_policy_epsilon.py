"""Optional seeded random-move rate per brain (policy_epsilon): arena, scoring, metadata."""

import asyncio
import json
import re

import numpy as np
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from minotaurus.brain import BrainError, load_brain, player
from minotaurus.engine.levels import load_level_by_id
from minotaurus.server.app import create_app
from minotaurus.server.arena import run_arena
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.evaluate import success_rate
from minotaurus.trainer.export import export_qtable
from minotaurus.trainer.qtable import QTableAgent
from minotaurus.trainer.train import train
from tests.test_server import run_messages, upload
from tests.test_trainer import small_qtable_config


def make_brain(tmp_path, epsilon: str | None, name="b.onnx"):
    """An untrained Q-table brain: without random moves it always picks move 0 (up)."""
    meta = None if epsilon is None else {"policy_epsilon": epsilon}
    path = tmp_path / name
    export_qtable(QTableAgent(0.1, 0.9, 1.0, 0.1, 0.9), path, "t", ["easy-01"], extra_meta=meta)
    return path


def moves(play, n=40):
    obs = np.zeros(77, dtype=np.float32)
    chosen = []
    for _ in range(n):
        chosen.append(play(obs))
    return chosen


def test_policy_epsilon_defaults_to_0_and_is_a_probability():
    assert ConfigFile.model_validate(small_qtable_config()).policy_epsilon == 0.0
    data = small_qtable_config()
    data["policy_epsilon"] = 1.5
    with pytest.raises(ValidationError, match="policy_epsilon"):
        ConfigFile.model_validate(data)


def test_a_brain_without_the_setting_is_never_changed(tmp_path):
    brain = load_brain(make_brain(tmp_path, None))
    assert brain.policy_epsilon == 0.0
    assert player(brain, seed="any") is brain  # the very same callable: plain argmax


def test_bad_policy_epsilon_metadata_is_refused(tmp_path):
    for i, bad in enumerate(["abc", "1.5", "-0.1", "nan", "inf", "", "1.0000001"]):
        message = f"bad policy_epsilon {bad!r}: must be a number from 0 to 1"
        with pytest.raises(BrainError, match=re.escape(message)):
            load_brain(make_brain(tmp_path, bad, name=f"bad{i}.onnx"))


def test_policy_epsilon_0_and_1_are_accepted(tmp_path):
    assert load_brain(make_brain(tmp_path, "0", name="zero.onnx")).policy_epsilon == 0.0
    assert load_brain(make_brain(tmp_path, "1", name="one.onnx")).policy_epsilon == 1.0


def test_random_moves_are_seeded(tmp_path):
    brain = load_brain(make_brain(tmp_path, "0.5"))
    assert brain.policy_epsilon == 0.5
    first = moves(player(brain, seed="s1"))
    assert first == moves(player(brain, seed="s1"))  # same seed, same moves
    assert first != moves(player(brain, seed="s2"))
    assert set(first) - {0}  # some moves are random (the brain alone always picks 0)
    assert 0 in first


def test_an_override_rate_is_used_instead_of_the_metadata(tmp_path):
    brain = load_brain(make_brain(tmp_path, None))
    assert set(moves(player(brain, seed="s", epsilon=1.0))) - {0}
    assert player(brain, seed="s", epsilon=0.0) is brain


def test_training_writes_the_rate_into_the_brain(tmp_path):
    data = small_qtable_config(episodes=2)
    data["policy_epsilon"] = 0.1
    config = ConfigFile.model_validate(data)
    run = train(config, config.resolve_levels(), run_dir=tmp_path / "r")
    assert load_brain(run / "brain.onnx").policy_epsilon == 0.1
    plain = ConfigFile.model_validate(small_qtable_config(episodes=2))
    run = train(plain, plain.resolve_levels(), run_dir=tmp_path / "p")
    assert "policy_epsilon" not in load_brain(run / "brain.onnx").meta


def test_scoring_uses_the_brains_rate_reproducibly(tmp_path):
    level = load_level_by_id("easy-01")
    stuck = load_brain(make_brain(tmp_path, None, name="stuck.onnx"))
    assert success_rate(stuck, (level,)) == 0.0  # always up, into the wall
    wanders = load_brain(make_brain(tmp_path, "1.0", name="wanders.onnx"))
    rates = []
    for _ in range(2):
        rates.append(success_rate(wanders, (level,) * 20, seed=3))
    assert rates[0] == rates[1]
    assert success_rate(wanders, (level,) * 20, seed=3, policy_epsilon=0.0) == 0.0


def test_the_arena_server_replays_a_random_brain_exactly(tmp_path):
    client = TestClient(create_app(tick_seconds=0.0))
    assert upload(client, make_brain(tmp_path, "0.5")).status_code == 200
    first = run_messages(client, "easy-01")
    again = run_messages(client, "easy-01")
    assert [m.model_dump() for m in first] == [m.model_dump() for m in again]
    ticks = [(m.x, m.y) for m in first if m.type == "tick"]
    assert len(set(ticks)) > 1  # it moved: the random moves were applied


def test_the_arena_server_runs_a_plain_brain_as_before(tmp_path):
    client = TestClient(create_app(tick_seconds=0.0))
    path = make_brain(tmp_path, None)
    assert upload(client, path).status_code == 200
    served = run_messages(client, "easy-01")

    async def direct():
        out = []
        async for message in run_arena(load_level_by_id("easy-01"), load_brain(path), 0.0):
            out.append(json.loads(message.model_dump_json(exclude_none=True)))
        return out

    expected = asyncio.run(direct())
    got = []
    for message in served:
        got.append(json.loads(message.model_dump_json(exclude_none=True)))
    assert got == expected
