from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from minotaurus.engine.levels import load_portal_levels
from minotaurus.server.app import create_app
from minotaurus.server.store import Store
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.train import train

EXAMPLES = Path(__file__).resolve().parents[1] / "data" / "examples"


@pytest.fixture(scope="module")
def trained_brain(tmp_path_factory) -> Path:
    config = ConfigFile.model_validate_json((EXAMPLES / "qtable-brain.json").read_text())
    folder = tmp_path_factory.mktemp("trained")
    return (
        train(config, config.resolve_levels(), run_dir=folder / "run", log_every=500) / "brain.onnx"
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(tick_seconds=0.0))


def load(client, path: Path) -> str:
    return client.post("/api/brain", files={"file": ("b.onnx", path.read_bytes())}).json()["id"]


def test_run_all_plays_every_portal_level_and_counts_the_finished(client, trained_brain):
    brain_id = load(client, trained_brain)
    response = client.post(f"/api/brains/{brain_id}/run-all")
    assert response.status_code == 200
    batch = response.json()
    assert batch["brain_id"] == brain_id
    assert batch["total"] == len(load_portal_levels())
    levels = {}
    for row in batch["results"]:
        levels[row["level_id"]] = row
    assert levels["easy-01"]["status"] == "finished"
    assert levels["easy-01"]["steps"] == 13
    finished = 0
    for row in batch["results"]:
        if row["status"] == "finished":
            finished += 1
    assert batch["finished"] == finished >= 1


def test_run_all_gives_the_same_result_as_playing_a_level_by_hand(client, trained_brain):
    from starlette.websockets import WebSocketDisconnect

    brain_id = load(client, trained_brain)
    batch = client.post(f"/api/brains/{brain_id}/run-all").json()
    with client.websocket_connect(f"/ws/run?level_id=easy-02&brain_id={brain_id}") as socket:
        last = None
        while True:
            try:
                last = socket.receive_json()
            except WebSocketDisconnect:
                break
    for row in batch["results"]:
        if row["level_id"] == "easy-02":
            assert row["status"] == last["status"]
            assert row["steps"] == last["steps"]


def test_batches_are_kept_per_brain_newest_first(client, trained_brain):
    brain_id = load(client, trained_brain)
    first = client.post(f"/api/brains/{brain_id}/run-all").json()
    second = client.post(f"/api/brains/{brain_id}/run-all").json()
    listed = client.get(f"/api/brains/{brain_id}/batches").json()
    assert [row["id"] for row in listed] == [second["id"], first["id"]]
    assert client.get(f"/api/brains/{'1' * 64}/batches").json() == []


def test_run_all_with_an_unknown_brain_is_a_404(client):
    assert client.post(f"/api/brains/{'0' * 64}/run-all").status_code == 404
    assert client.post("/api/brains/nope/run-all").status_code == 404


def test_run_all_is_refused_while_a_run_is_going(client, trained_brain):
    brain_id = load(client, trained_brain)
    client.app.state.running = True
    response = client.post(f"/api/brains/{brain_id}/run-all")
    assert response.status_code == 400
    assert "already" in response.json()["message"]
    client.app.state.running = False


def test_a_batch_survives_a_restart(tmp_path, trained_brain):
    first = TestClient(create_app(tick_seconds=0.0, data_dir=tmp_path))
    brain_id = load(first, trained_brain)
    batch = first.post(f"/api/brains/{brain_id}/run-all").json()
    second = TestClient(create_app(tick_seconds=0.0, data_dir=tmp_path))
    assert [row["id"] for row in second.get(f"/api/brains/{brain_id}/batches").json()] == [
        batch["id"]
    ]


def test_the_store_keeps_batches():
    store = Store()
    store.add_batch(
        {
            "id": "b1",
            "brain_id": "a" * 64,
            "date": "2026-11-24T10:00:00Z",
            "total": 2,
            "finished": 1,
            "results": [{"level_id": "x"}],
        }
    )
    assert store.list_batches("a" * 64)[0]["results"] == [{"level_id": "x"}]
    assert store.list_batches("b" * 64) == []
