"""The loader's per-step time check: an untimed warm-up call first, then the timed checks."""

import time

import pytest
from typer.testing import CliRunner

from minotaurus.brain import BrainError, load_brain, onnx_brain
from minotaurus.cli import app
from minotaurus.trainer.export import export_qtable
from minotaurus.trainer.qtable import QTableAgent


class SlowFirstCall:
    """An onnxruntime session whose first run takes 0.2 s, as a cold start can."""

    def __init__(self, *args, **kwargs):
        self.inner = REAL_SESSION(*args, **kwargs)
        self.calls = 0

    def get_inputs(self):
        return self.inner.get_inputs()

    def run(self, *args, **kwargs):
        self.calls += 1
        if self.calls == 1:
            time.sleep(0.2)
        return self.inner.run(*args, **kwargs)


REAL_SESSION = onnx_brain.ort.InferenceSession


@pytest.fixture
def brain_file(tmp_path):
    path = tmp_path / "q.onnx"
    export_qtable(QTableAgent(0.1, 0.9, 1.0, 0.1, 0.9), path, "tiny", ["easy-01"])
    return path


def test_a_slow_first_call_no_longer_fails_check_brain(brain_file, monkeypatch):
    monkeypatch.setattr(onnx_brain.ort, "InferenceSession", SlowFirstCall)
    result = CliRunner().invoke(app, ["check-brain", str(brain_file)])
    assert result.exit_code == 0, result.output
    assert "OK: tiny (qtable)" in result.output


def test_the_warm_up_call_is_untimed_but_the_test_run_is_still_timed(brain_file, monkeypatch):
    monkeypatch.setattr(onnx_brain.ort, "InferenceSession", SlowFirstCall)
    brain = load_brain(brain_file)
    assert brain.session.calls == 2  # one untimed warm-up, one timed test run
    with pytest.raises(BrainError, match="too slow"):
        load_brain(brain_file, time_limit_s=1e-9)  # the timed test run still applies


def test_a_slow_step_after_loading_is_still_refused(brain_file):
    brain = load_brain(brain_file)
    brain.time_limit_s = 1e-9
    with pytest.raises(BrainError, match="too slow"):
        brain.scores([0.0] * 77)
