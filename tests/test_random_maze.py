import pytest
from fastapi.testclient import TestClient

from minotaurus.server.app import create_app
from tests.test_server_brains import made, run_messages, upload  # noqa: F401


@pytest.fixture
def client():
    return TestClient(create_app(tick_seconds=0.0))


def test_a_random_maze_has_the_asked_size_and_a_seed_in_its_id(client):
    response = client.post("/api/mazes/random", json={"size": 13, "seed": 4821})
    assert response.status_code == 200
    level = response.json()
    assert level["id"] == "gen-13-4821"
    assert level["group"] == "random"
    assert level["difficulty"] == "medium"
    assert len(level["grid"]) == 13 and len(level["grid"][0]) == 13
    assert level["step_limit"] >= 1
    assert "4821" in level["name"]


def test_the_same_seed_gives_the_same_maze_and_no_seed_draws_one(client):
    one = client.post("/api/mazes/random", json={"size": 9, "seed": 7}).json()
    two = client.post("/api/mazes/random", json={"size": 9, "seed": 7}).json()
    assert one == two
    drawn = client.post("/api/mazes/random", json={"size": 9}).json()
    assert drawn["id"].startswith("gen-9-")


def test_the_options_change_the_id(client):
    level = client.post(
        "/api/mazes/random",
        json={"size": 9, "seed": 3, "random_start": True, "border_exit": True},
    ).json()
    assert level["id"] == "gen-9-3-r-b"


@pytest.mark.parametrize("size", [3, 8, 43, 100])
def test_a_bad_size_is_refused_with_a_message(client, size):
    response = client.post("/api/mazes/random", json={"size": size})
    assert response.status_code == 400
    assert "size" in response.json()["message"]


def test_a_missing_size_or_unknown_field_is_refused(client):
    assert client.post("/api/mazes/random", json={}).status_code == 400
    assert client.post("/api/mazes/random", json={"size": 9, "x": 1}).status_code == 400


def test_a_generated_level_can_be_run_by_its_id(client, made):  # noqa: F811
    brain_id = upload(client, made["onnx"], name="b.onnx").json()["id"]
    level = client.post("/api/mazes/random", json={"size": 9, "seed": 5}).json()
    messages = run_messages(client, level["id"], brain_id)
    assert messages[0].type == "run_started"
    assert messages[-1].type == "result"


def test_running_a_bad_generated_id_reports_an_error(client, made):  # noqa: F811
    brain_id = upload(client, made["onnx"], name="b.onnx").json()["id"]
    messages = run_messages(client, "gen-8-1", brain_id)
    assert messages[-1].type == "error"
