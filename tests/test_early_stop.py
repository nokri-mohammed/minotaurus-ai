"""Early stop (2026-11-24): patience = validation checks in a row without a better score."""

import json

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from minotaurus.brain import load_brain
from minotaurus.cli import app
from minotaurus.trainer import train as train_module
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.train import train
from tests.test_trainer import small_qtable_config


def generated_config(episodes: int = 40, eval_every: int = 2, patience=None) -> dict:
    data = small_qtable_config(episodes)
    data["levels"] = {
        "generated": {"size": 9, "maze_seed": 1, "train": 4, "validation": 2, "test": 2}
    }
    data["eval_every"] = eval_every
    if patience is not None:
        data["patience"] = patience
    return data


def scripted(monkeypatch, scores: list[float]) -> list[int]:
    """Make the validation checks return `scores` in order (then the last one again)."""
    calls = []

    def fake(agent, levels, window, obs_version=1):
        calls.append(1)
        index = len(calls) - 1
        if index >= len(scores):
            index = len(scores) - 1
        return scores[index], 0

    monkeypatch.setattr(train_module, "validation_check", fake)
    return calls


def rows(run_dir) -> list[dict]:
    out = []
    for text in (run_dir / "metrics.jsonl").read_text().splitlines():
        out.append(json.loads(text))
    return out


def run(data, tmp_path, name="r"):
    config = ConfigFile.model_validate(data)
    pools = config.resolve_pools()
    return train(config, pools.train, run_dir=tmp_path / name, pools=pools)


# ---- config ----


def test_patience_is_off_by_default_and_recorded():
    config = ConfigFile.model_validate(generated_config())
    assert config.patience is None
    assert config.training_options(config.resolve_pools())["patience"] is None


def test_patience_must_be_at_least_one():
    with pytest.raises(ValidationError, match="patience"):
        ConfigFile.model_validate(generated_config(patience=0))


def test_patience_needs_validation_checks():
    with pytest.raises(ValidationError, match="patience"):
        ConfigFile.model_validate(generated_config(eval_every=0, patience=3))
    data = small_qtable_config()  # hand-made levels: no validation mazes
    data["patience"] = 3
    with pytest.raises(ValidationError, match="patience"):
        ConfigFile.model_validate(data)


# ---- training ----


SCORES = [0.2, 0.5, 0.5, 0.4, 0.5, 0.9]  # checks at tries 2, 4, 6, 8, 10, 12


def test_training_stops_after_patience_checks_without_a_better_score(tmp_path, monkeypatch):
    calls = scripted(monkeypatch, SCORES)
    run_dir = run(generated_config(patience=3), tmp_path)
    # 0.2 and 0.5 improve; then 0.5 (a tie is not better), 0.4, 0.5: three checks -> stop at 10
    assert len(calls) == 5
    lines = rows(run_dir)
    tries = [row["episode"] for row in lines if "avg_reward" in row]
    assert max(tries) == 10
    chosen = lines[-1]
    assert chosen["stopped_at_episode"] == 10
    assert chosen["exported_episode"] == 10  # the tie at 0.5 keeps the later brain, as before
    assert chosen["validation_success"] == 0.5
    training = json.loads(load_brain(run_dir / "brain.onnx").meta["training"])
    assert training["patience"] == 3 and training["stopped_at_episode"] == 10


def test_without_patience_training_runs_to_the_end(tmp_path, monkeypatch):
    calls = scripted(monkeypatch, SCORES)
    run_dir = run(generated_config(), tmp_path)
    assert len(calls) == 20  # every 2 tries up to 40
    chosen = rows(run_dir)[-1]
    assert "stopped_at_episode" not in chosen
    assert chosen["exported_episode"] == 40 and chosen["validation_success"] == 0.9
    training = json.loads(load_brain(run_dir / "brain.onnx").meta["training"])
    assert training["patience"] is None and training["stopped_at_episode"] is None


def test_a_late_improvement_resets_the_count(tmp_path, monkeypatch):
    calls = scripted(monkeypatch, [0.1, 0.1, 0.3, 0.3, 0.3])
    run(generated_config(patience=3), tmp_path)
    # 0.1 improves, 0.1 (1), 0.3 improves (back to 0), 0.3 (1), 0.3 (2), 0.3 (3) -> stop
    assert len(calls) == 6


def test_the_train_command_says_it_stopped_early(tmp_path, monkeypatch):
    scripted(monkeypatch, SCORES)
    path = tmp_path / "c.json"
    path.write_text(json.dumps(generated_config(patience=3)))
    result = CliRunner().invoke(
        app, ["train", "--config", str(path), "--runs-dir", str(tmp_path / "runs"), "--no-plot"]
    )
    assert result.exit_code == 0, result.output
    assert "stopped early at try 10" in result.output
