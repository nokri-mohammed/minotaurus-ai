import io
import tarfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter
from starlette.websockets import WebSocketDisconnect

from minotaurus.bundle import build_bundle
from minotaurus.server.app import create_app
from minotaurus.server.messages import RunMessage
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.plot import plot_metrics
from minotaurus.trainer.train import train

RUN_MESSAGE = TypeAdapter(RunMessage)


@pytest.fixture(scope="module")
def made(tmp_path_factory) -> dict:
    """A trained run with its graph, a plain brain.onnx and its bundle.tar."""
    config = ConfigFile.model_validate_json(
        (
            Path(__file__).resolve().parents[1] / "data" / "examples" / "qtable-brain.json"
        ).read_text()
    )
    folder = tmp_path_factory.mktemp("made")
    run_dir = train(config, config.resolve_levels(), run_dir=folder / "run", log_every=50)
    plot_metrics(run_dir / "metrics.jsonl", run_dir / "training.png", title=config.name)
    bundle = build_bundle(run_dir)
    return {"onnx": run_dir / "brain.onnx", "bundle": bundle}


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(tick_seconds=0.0))


def upload(client, path: Path | None = None, content: bytes | None = None, name="b"):
    data = content if content is not None else path.read_bytes()
    return client.post("/api/brain", files={"file": (name, data)})


def run_messages(client, level_id: str, brain_id: str | None = None) -> list:
    url = f"/ws/run?level_id={level_id}"
    if brain_id is not None:
        url += f"&brain_id={brain_id}"
    messages = []
    with client.websocket_connect(url) as socket:
        while True:
            try:
                text = socket.receive_text()
            except WebSocketDisconnect:
                break
            messages.append(RUN_MESSAGE.validate_json(text))
    return messages


def test_a_plain_brain_gets_an_id_from_its_hash_and_has_no_recipe(client, made):
    import hashlib

    reply = upload(client, made["onnx"], name="b.onnx").json()
    assert reply["id"] == hashlib.sha256(made["onnx"].read_bytes()).hexdigest()
    assert reply["has_recipe"] is False
    assert reply["method"] == "qtable"


def test_a_bundle_gets_the_same_id_and_has_a_recipe(client, made):
    plain = upload(client, made["onnx"], name="b.onnx").json()
    bundled = upload(client, made["bundle"], name="b.tar").json()
    assert bundled["id"] == plain["id"]
    assert bundled["has_recipe"] is True
    assert len(client.get("/api/brains").json()) == 1  # the same brain, one row


def test_the_list_shows_every_loaded_brain(client, made):
    upload(client, made["bundle"])
    listed = client.get("/api/brains").json()
    assert [row["name"] for row in listed] == ["qtable-easy"]
    assert set(listed[0]) == {"id", "name", "method", "has_recipe", "added_at"}


def test_the_recipe_carries_the_config_scores_and_graph_flag(client, made):
    brain_id = upload(client, made["bundle"]).json()["id"]
    recipe = client.get(f"/api/brains/{brain_id}/recipe").json()
    assert recipe["config"]["name"] == "qtable-easy"
    assert recipe["has_graph"] is True
    assert "bundle_version" in recipe
    graph = client.get(f"/api/brains/{brain_id}/graph.png")
    assert graph.status_code == 200
    assert graph.headers["content-type"] == "image/png"
    assert graph.content[:4] == b"\x89PNG"


def test_the_metrics_give_the_training_curves(client, made):
    brain_id = upload(client, made["bundle"]).json()["id"]
    metrics = client.get(f"/api/brains/{brain_id}/metrics").json()
    assert len(metrics["points"]) > 0
    first = metrics["points"][0]
    assert first["episode"] > 0
    assert 0 <= first["success_rate"] <= 1
    assert "loss" not in first or first["loss"] is not None  # an empty value is left out, not null
    assert isinstance(metrics["quiz"], list)


def test_a_brain_can_be_downloaded_as_the_file_that_was_uploaded(client, made):
    bundle_bytes = made["bundle"].read_bytes()
    brain_id = upload(client, made["bundle"]).json()["id"]
    response = client.get(f"/api/brains/{brain_id}/download")
    assert response.status_code == 200
    assert response.content == bundle_bytes
    disposition = response.headers["content-disposition"]
    assert disposition.startswith("attachment;")
    assert f"-{brain_id[:8]}.tar" in disposition


def test_a_plain_brain_downloads_as_onnx_and_an_unknown_one_is_404(client, made):
    onnx_bytes = made["onnx"].read_bytes()
    brain_id = upload(client, made["onnx"], name="b.onnx").json()["id"]
    response = client.get(f"/api/brains/{brain_id}/download")
    assert response.content == onnx_bytes
    assert f"-{brain_id[:8]}.onnx" in response.headers["content-disposition"]
    assert client.get(f"/api/brains/{'0' * 64}/download").status_code == 404
    assert client.get("/api/brains/not-an-id/download").status_code == 404


def test_a_plain_brain_has_no_recipe_page(client, made):
    brain_id = upload(client, made["onnx"]).json()["id"]
    assert client.get(f"/api/brains/{brain_id}/recipe").status_code == 404
    assert client.get(f"/api/brains/{brain_id}/graph.png").status_code == 404
    assert client.get(f"/api/brains/{brain_id}/metrics").status_code == 404


def test_an_unknown_brain_id_is_a_404(client):
    assert client.get(f"/api/brains/{'0' * 64}/recipe").status_code == 404
    assert client.get("/api/brains/not-an-id/recipe").status_code == 404


def test_a_bad_bundle_is_refused_with_the_reason(client, made):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w") as tar:
        info = tarfile.TarInfo("../evil")
        info.size = 1
        tar.addfile(info, io.BytesIO(b"x"))
    response = upload(client, content=out.getvalue(), name="evil.tar")
    assert response.status_code == 400
    assert "allowed file name" in response.json()["message"]
    assert client.get("/api/brains").json() == []


def test_a_run_names_its_brain_and_needs_no_current_one(client, made):
    first = upload(client, made["bundle"]).json()["id"]
    # a second, different brain becomes the "current" one, but the run asks for the first
    client.app.state.brain = None
    messages = run_messages(client, "easy-01", first)
    assert messages[-1].status == "finished"


def test_a_run_with_an_unknown_brain_id_sends_an_error(client, made):
    upload(client, made["bundle"])
    messages = run_messages(client, "easy-01", "f" * 64)
    assert [m.type for m in messages] == ["error"]
    assert "not loaded" in messages[0].message


def test_loaded_brains_survive_a_restart_with_a_database_file(tmp_path, made):
    first = TestClient(create_app(tick_seconds=0.0, data_dir=tmp_path))
    brain_id = upload(first, made["bundle"]).json()["id"]
    second = TestClient(create_app(tick_seconds=0.0, data_dir=tmp_path))
    assert [row["id"] for row in second.get("/api/brains").json()] == [brain_id]
    assert run_messages(second, "easy-01", brain_id)[-1].status == "finished"
