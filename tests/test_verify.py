import json
from pathlib import Path

import pytest

from minotaurus.bundle import Bundle, build_bundle, read_bundle
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.train import train
from minotaurus.verify import verify_bundle
from tests.test_trainer import small_qtable_config

GENERATED = {
    "size": 9,
    "maze_seed": 1,
    "train": 8,
    "validation": 6,
    "test": 6,
}


def generated_config(**generated) -> ConfigFile:
    data = small_qtable_config(episodes=300)
    data["levels"] = {"generated": {**GENERATED, **generated}}
    return ConfigFile.model_validate(data)


@pytest.fixture(scope="module")
def made(tmp_path_factory) -> bytes:
    """The bytes of a real bundle trained on generated mazes, so it has scores to check."""
    config = generated_config()
    pools = config.resolve_pools()
    run_dir = train(config, pools.train, tmp_path_factory.mktemp("runs"), pools=pools)
    return build_bundle(run_dir, tmp_path_factory.mktemp("out") / "b.tar").read_bytes()


@pytest.fixture
def bundle(made) -> Bundle:
    return read_bundle(made)


def test_an_honest_bundle_is_verified(bundle):
    result = verify_bundle(bundle)
    assert result.status == "verified"
    names = []
    for check in result.checks:
        assert check.match is True
        names.append(check.name)
    assert {"validation", "test", "hand-made levels finished", "test steps"} <= set(names)
    assert result.not_checked == ["train"]


def test_a_better_score_than_the_brain_earns_is_caught(bundle):
    scores = json.loads(bundle.files["scores.json"])
    scores["test"] = 1.0 if scores["test"] < 1.0 else 0.0  # a score the brain does not get
    bundle.files["scores.json"] = json.dumps(scores).encode()
    result = verify_bundle(bundle)
    assert result.status == "mismatch"
    assert "test" in result.message
    failed = [c.name for c in result.checks if not c.match]
    assert failed == ["test"]


def test_a_changed_hand_made_result_is_caught(bundle):
    fixed = json.loads(bundle.files["fixed_levels.json"])
    first = next(iter(fixed))
    fixed[first] = not fixed[first]
    bundle.files["fixed_levels.json"] = json.dumps(fixed).encode()
    assert verify_bundle(bundle).status == "mismatch"


def test_settings_that_name_other_mazes_are_caught(bundle):
    other = generated_config(maze_seed=2)
    bundle.config = other
    result = verify_bundle(bundle)
    assert result.status == "mismatch"
    assert "different mazes" in result.message


def test_a_bundle_with_no_claimed_scores_is_unavailable(bundle):
    for name in ("scores.json", "fixed_levels.json", "test_stats.json"):
        bundle.files.pop(name, None)
    result = verify_bundle(bundle)
    assert result.status == "unavailable"
    assert result.checks == []


def test_a_hand_made_config_has_no_exam_to_repeat(tmp_path_factory):
    config = ConfigFile.model_validate(small_qtable_config(episodes=20))
    run_dir = train(config, config.resolve_levels(), tmp_path_factory.mktemp("runs"))
    (Path(run_dir) / "scores.json").write_text(json.dumps({"train": 1, "validation": 1, "test": 1}))
    bundle = read_bundle(build_bundle(run_dir, run_dir / "b.tar").read_bytes())
    assert verify_bundle(bundle).status == "unavailable"


# ---- the server endpoint ----


def test_the_endpoint_verifies_a_bundle_and_keeps_the_answer(made):
    from fastapi.testclient import TestClient

    from minotaurus.server.app import create_app

    app = create_app(tick_seconds=0.0)
    client = TestClient(app)
    brain_id = client.post("/api/brain", files={"file": ("b.tar", made)}).json()["id"]
    first = client.post(f"/api/brains/{brain_id}/verify")
    assert first.status_code == 200
    assert first.json()["status"] == "verified"
    assert app.state.store.get_verification(brain_id) is not None
    assert client.post(f"/api/brains/{brain_id}/verify").json() == first.json()


def test_the_endpoint_refuses_an_unknown_or_plain_brain():
    from fastapi.testclient import TestClient

    from minotaurus.server.app import create_app

    client = TestClient(create_app(tick_seconds=0.0))
    assert client.post(f"/api/brains/{'0' * 64}/verify").status_code == 404
    assert client.post("/api/brains/not-an-id/verify").status_code == 404


# ---- signing on the server ----


def test_a_signed_bundle_shows_its_author_and_when_it_was_first_seen(made, tmp_path_factory):
    from fastapi.testclient import TestClient

    from minotaurus.bundle import sign_bundle
    from minotaurus.server.app import create_app
    from minotaurus.signing import generate_key

    folder = tmp_path_factory.mktemp("sign")
    generate_key(folder / "k.key")
    path = folder / "b.tar"
    path.write_bytes(made)
    sign_bundle(path, folder / "k.key")

    app = create_app(tick_seconds=0.0)
    client = TestClient(app)
    plain_id = client.post("/api/brain", files={"file": ("b.tar", made)}).json()["id"]
    assert client.get(f"/api/brains/{plain_id}/recipe").json()["signed_by"] is None

    brain_id = client.post("/api/brain", files={"file": ("b.tar", path.read_bytes())}).json()["id"]
    recipe = client.get(f"/api/brains/{brain_id}/recipe").json()
    assert len(recipe["signed_by"]) == 16
    first = recipe["author_first_seen"]
    assert first
    assert client.get(f"/api/brains/{brain_id}/recipe").json()["author_first_seen"] == first


def test_a_new_file_for_the_same_brain_is_checked_again(made):
    from fastapi.testclient import TestClient

    from minotaurus.server.app import create_app

    app = create_app(tick_seconds=0.0)
    client = TestClient(app)
    brain_id = client.post("/api/brain", files={"file": ("b.tar", made)}).json()["id"]
    assert client.post(f"/api/brains/{brain_id}/verify").json()["status"] == "verified"
    assert app.state.store.get_verification(brain_id) is not None
    client.post("/api/brain", files={"file": ("b.tar", made)})  # uploaded again
    assert app.state.store.get_verification(brain_id) is None


def test_a_bundle_with_a_broken_signature_is_refused_on_upload(made, tmp_path_factory):
    from fastapi.testclient import TestClient

    from minotaurus.bundle import sign_bundle
    from minotaurus.server.app import create_app
    from minotaurus.signing import generate_key

    folder = tmp_path_factory.mktemp("broken")
    generate_key(folder / "k.key")
    path = folder / "b.tar"
    path.write_bytes(made)
    sign_bundle(path, folder / "k.key")
    data = bytearray(path.read_bytes())
    marker = data.rfind(b'"signature": "')
    data[marker + 14] = ord("0") if data[marker + 14] != ord("0") else ord("1")
    client = TestClient(create_app(tick_seconds=0.0))
    response = client.post("/api/brain", files={"file": ("b.tar", bytes(data))})
    assert response.status_code == 400
    assert "signature is not good" in response.json()["message"]
