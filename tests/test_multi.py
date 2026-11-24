import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from minotaurus.cli import app
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.multi import (
    SeedResult,
    default_parallel,
    pick_best,
    run_seeds,
)

EXAMPLES = Path(__file__).resolve().parents[1] / "data" / "examples"


def tiny_config(**extra) -> dict:
    data = json.loads((EXAMPLES / "qtable-brain.json").read_text())
    data["episodes"] = 30
    data.update(extra)
    return data


def result(seed, success=0.5, steps=20.0, validation=None, test=None) -> SeedResult:
    scores = None
    if validation is not None:
        scores = {"train": 1.0, "validation": validation, "test": test if test is not None else 0.0}
    return SeedResult(
        seed=seed,
        run_dir=f"seed-{seed}",
        seconds=1.0,
        success_rate=success,
        avg_steps=steps,
        avg_path_ratio=None,
        scores=scores,
    )


# ---- config ----


def test_config_seeds_and_parallel_are_optional():
    plain = ConfigFile.model_validate(tiny_config())
    assert plain.seeds is None and plain.parallel is None
    many = ConfigFile.model_validate(tiny_config(seeds=[1, 2, 3], parallel=2))
    assert many.seeds == [1, 2, 3] and many.parallel == 2


def test_config_seeds_must_be_different_and_not_empty():
    with pytest.raises(ValidationError, match="seeds"):
        ConfigFile.model_validate(tiny_config(seeds=[1, 1]))
    with pytest.raises(ValidationError, match="seeds"):
        ConfigFile.model_validate(tiny_config(seeds=[]))
    with pytest.raises(ValidationError, match="parallel"):
        ConfigFile.model_validate(tiny_config(parallel=0))


def test_for_seed_keeps_the_recipe_and_drops_the_seed_list():
    config = ConfigFile.model_validate(tiny_config(seeds=[4, 5], parallel=2))
    one = config.for_seed(5)
    assert one.seed == 5 and one.name == config.name
    assert one.seeds is None and one.parallel is None
    assert one.qtable == config.qtable and one.episodes == config.episodes


# ---- choosing the best seed ----


def test_best_seed_is_the_highest_validation_score():
    results = [result(1, validation=0.7), result(2, validation=0.9), result(3, validation=0.8)]
    assert pick_best(results).seed == 2


def test_a_tie_goes_to_fewer_steps_then_the_lower_seed():
    tie = [result(1, steps=30.0, validation=0.8), result(2, steps=25.0, validation=0.8)]
    assert pick_best(tie).seed == 2
    same = [result(3, steps=25.0, validation=0.8), result(2, steps=25.0, validation=0.8)]
    assert pick_best(same).seed == 2


def test_test_scores_never_decide():
    results = [result(1, validation=0.5, test=1.0), result(2, validation=0.6, test=0.0)]
    assert pick_best(results).seed == 2


def test_without_validation_the_last_success_rate_decides():
    results = [result(1, success=0.4), result(2, success=0.9)]
    assert pick_best(results).seed == 2


def test_default_parallel_is_never_more_than_the_seeds_or_the_cores():
    assert default_parallel(1) == 1
    assert 1 <= default_parallel(1000) <= 1000


# ---- running ----


def test_run_seeds_trains_each_seed_in_its_own_folder(tmp_path):
    config = ConfigFile.model_validate(tiny_config())
    results = list(run_seeds(config, [1, 2], 2, tmp_path, log_every=10, plot=False))
    assert sorted(r.seed for r in results) == [1, 2]
    for r in results:
        assert (Path(r.run_dir) / "brain.onnx").exists()
        assert Path(r.run_dir).parent == tmp_path
        recorded = json.loads((Path(r.run_dir) / "config.json").read_text())
        assert recorded["seed"] == r.seed and "seeds" not in recorded


def test_the_cli_trains_several_seeds_and_keeps_the_best(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps(tiny_config()))
    out = tmp_path / "runs"
    result_ = CliRunner().invoke(
        app,
        [
            "train",
            "--config",
            str(path),
            "--runs-dir",
            str(out),
            "--seeds",
            "2",
            "--parallel",
            "2",
            "--no-plot",
        ],
    )
    assert result_.exit_code == 0, result_.output
    assert "best seed" in result_.output
    folder = next((out / "qtable-easy").iterdir())
    assert (folder / "best-brain.onnx").exists()
    summary = json.loads((folder / "summary.json").read_text())
    assert [row["seed"] for row in summary["seeds"]] == [1, 2]
    assert summary["best_seed"] in (1, 2)


def test_run_seeds_reports_the_tries_of_each_seed(tmp_path):
    config = ConfigFile.model_validate(tiny_config())
    seen = []

    def on_progress(seed, episode):
        seen.append((seed, episode))

    results = list(
        run_seeds(config, [1, 2], 2, tmp_path, log_every=10, plot=False, on_progress=on_progress)
    )
    assert len(results) == 2
    for seed in (1, 2):
        tries = [episode for who, episode in seen if who == seed]
        assert tries == [10, 20, 30]


def test_the_cli_shows_plain_lines_when_not_on_a_terminal(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps(tiny_config()))
    out = CliRunner().invoke(
        app, ["train", "--config", str(path), "--runs-dir", str(tmp_path / "r"), "--no-plot"]
    )
    assert out.exit_code == 0, out.output
    assert "episode 10/30" in out.output
    assert "\r" not in out.output
