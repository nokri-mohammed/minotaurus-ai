from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter
from starlette.websockets import WebSocketDisconnect

from minotaurus.brain import BrainError
from minotaurus.server.app import create_app
from minotaurus.server.messages import RunMessage
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.export import export_qtable
from minotaurus.trainer.qtable import QTableAgent
from minotaurus.trainer.train import train

EXAMPLES = Path(__file__).resolve().parents[1] / "data" / "examples"
RUN_MESSAGE = TypeAdapter(RunMessage)


@pytest.fixture(scope="module")
def trained_brain(tmp_path_factory) -> Path:
    """A real trained Q-table brain (the example config), made once for the whole file."""
    config = ConfigFile.model_validate_json((EXAMPLES / "qtable-brain.json").read_text())
    folder = tmp_path_factory.mktemp("trained")
    run_dir = train(config, config.resolve_levels(), run_dir=folder / "run", log_every=500)
    return run_dir / "brain.onnx"


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(tick_seconds=0.0))


def upload(
    client: TestClient, path: Path | None = None, content: bytes | None = None, name="b.onnx"
):
    data = content if content is not None else path.read_bytes()
    return client.post("/api/brain", files={"file": (name, data)})


def run_messages(client: TestClient, level_id: str) -> list:
    messages = []
    with client.websocket_connect(f"/ws/run?level_id={level_id}") as socket:
        while True:
            try:
                text = socket.receive_text()
            except WebSocketDisconnect:
                break
            messages.append(RUN_MESSAGE.validate_json(text))
    return messages


# ---- levels ----


def test_levels_lists_the_level_files(client):
    response = client.get("/api/levels")
    assert response.status_code == 200
    first = response.json()[0]
    assert first["id"] == "easy-01"
    assert first["step_limit"] == 52
    assert len(first["grid"]) == 9


def test_levels_list_the_test_mazes_inside_their_difficulty(client):
    ids = []
    for level in client.get("/api/levels").json():
        ids.append(level["id"])
    assert len(ids) == 19
    assert ids[:3] == ["easy-01", "easy-02", "test-09-01"]
    assert ids[-1] == "impossible-01"


# ---- brain upload ----


def test_upload_a_trained_brain(client, trained_brain):
    response = upload(client, trained_brain)
    assert response.status_code == 200
    assert response.json() == {"name": "qtable-easy", "method": "qtable"}


def test_upload_that_is_not_a_brain_is_refused_with_a_message(client):
    response = upload(client, content=b"this is not onnx")
    assert response.status_code == 400
    assert "not a valid ONNX file" in response.json()["message"]


def test_upload_that_is_too_big_is_refused(client):
    response = upload(client, content=b"x" * 1_000_001)
    assert response.status_code == 400
    assert "too big" in response.json()["message"]


def test_a_refused_upload_keeps_the_brain_that_was_loaded(client, trained_brain):
    upload(client, trained_brain)
    upload(client, content=b"not onnx")
    messages = run_messages(client, "easy-01")
    assert messages[-1].status == "finished"


# ---- runs ----


def test_a_trained_brain_finishes_the_level(client, trained_brain):
    upload(client, trained_brain)
    messages = run_messages(client, "easy-01")
    assert messages[0].type == "run_started"
    assert messages[0].step_limit == 52
    ticks = [m for m in messages if m.type == "tick"]
    assert [t.n for t in ticks] == list(range(1, len(ticks) + 1))
    result = messages[-1]
    assert result.type == "result"
    assert (result.status, result.steps) == ("finished", 13)
    assert result.seconds == pytest.approx(1.3)


def test_an_untrained_brain_times_out(client, tmp_path):
    path = tmp_path / "untrained.onnx"
    export_qtable(QTableAgent(0.1, 0.9, 1.0, 0.1, 0.9), path, "untrained", ["easy-01"])
    upload(client, path)
    messages = run_messages(client, "easy-01")
    assert messages[-1].status == "timed_out"
    assert messages[-1].steps == 52


def test_a_run_without_a_brain_sends_an_error(client):
    messages = run_messages(client, "easy-01")
    assert [m.type for m in messages] == ["error"]
    assert "Load a brain" in messages[0].message


def test_a_run_on_an_unknown_level_sends_an_error(client, trained_brain):
    upload(client, trained_brain)
    messages = run_messages(client, "nope-99")
    assert [m.type for m in messages] == ["error"]
    assert "nope-99" in messages[0].message


def test_a_brain_that_fails_during_the_run_ends_with_an_error_result():
    app = create_app(tick_seconds=0.0)

    def broken(obs):
        raise BrainError("brain is too slow: a step took more than 0.05 s")

    app.state.brain = broken
    messages = run_messages(TestClient(app), "easy-01")
    assert messages[-1].status == "error"
    assert "too slow" in messages[-1].message


def test_only_one_run_at_a_time(trained_brain):
    app = create_app(tick_seconds=0.0)
    client = TestClient(app)
    upload(client, trained_brain)
    app.state.running = True
    messages = run_messages(client, "easy-01")
    assert [m.type for m in messages] == ["error"]
    assert "already" in messages[0].message
    app.state.running = False
    assert run_messages(client, "easy-01")[-1].status == "finished"
