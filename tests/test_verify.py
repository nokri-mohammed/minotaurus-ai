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
