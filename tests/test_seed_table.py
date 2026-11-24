import json
from pathlib import Path

from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.evaluate import playthrough_stats
from minotaurus.trainer.multi import (
    SeedResult,
    collapse_warnings,
    results_table,
    run_seeds,
    table_note,
)
from minotaurus.trainer.train import train

EXAMPLES = Path(__file__).resolve().parents[1] / "data" / "examples"


def result(seed, **extra) -> SeedResult:
    values = {
        "seed": seed,
        "run_dir": f"seed-{seed}",
        "seconds": 90.0,
        "success_rate": 0.0,
        "avg_steps": 148.8,
        "avg_path_ratio": None,
        "scores": {"train": 0.6, "validation": 0.55, "test": 0.49},
        "fixed": {"easy-01": True, "easy-02": False},
    }
    values.update(extra)
    return SeedResult(**values)


def small_generated_config(episodes: int = 40) -> dict:
    data = json.loads((EXAMPLES / "qtable-brain.json").read_text())
    data["episodes"] = episodes
    data["levels"] = {
        "generated": {"size": 7, "maze_seed": 5, "train": 4, "validation": 2, "test": 2}
    }
    data["eval_every"] = 10
    return data


# ---- the table ----


def test_table_shows_where_the_saved_brain_came_from_and_its_path_ratio():
    one = result(3, saved_at=1000, tries_done=3250, test_steps=64.0, test_path_ratio=1.6)
    lines = results_table([one], one)
    assert "saved at" in lines[0]
    assert "finished" not in lines[0]
    assert "1000 of 3250" in lines[1]
    assert "1.60" in lines[1]
    assert "steps" not in lines[0]  # the average steps are in summary.json, not in the table
    assert "64.0" not in lines[1] and "148.8" not in lines[1]


def test_saved_at_without_the_number_of_tries_shows_just_the_try():
    one = result(3, saved_at=1000)
    assert "try 1000" in results_table([one], one)[1]


def test_the_note_under_the_table_says_why_that_try_was_picked():
    note = " ".join(table_note())
    assert "saved at" in note
    assert "best" in note and "validation" in note
    assert "tries the run did" in note


def test_table_falls_back_to_the_last_training_numbers_without_test_stats():
    one = result(1, scores=None, avg_steps=20.0, avg_path_ratio=1.5)
    lines = results_table([one], one)
    assert "1.50" in lines[1]
    assert "20.0" not in lines[1]
    assert "-" in lines[1].split()[1]  # no saved-at figure


def test_table_shows_a_dash_when_the_brain_never_finished_a_test_maze():
    one = result(2, saved_at=5000, test_steps=150.0, test_path_ratio=None)
    lines = results_table([one], one)
    assert "150.0" not in lines[1]
    assert " - " in lines[1]


# ---- collapse warnings ----


def test_a_seed_that_fell_apart_after_its_saved_try_gets_a_warning():
    fell = result(1, saved_at=250, saved_validation=0.27, final_validation=0.0)
    fine = result(3, saved_at=1000, saved_validation=0.55, final_validation=0.5)
    lines = collapse_warnings([fine, fell])
    assert len(lines) == 1
    assert "seed 1" in lines[0]
    assert "try 250" in lines[0]
    assert "27%" in lines[0]


def test_no_warning_without_validation_figures():
    assert collapse_warnings([result(1)]) == []


def test_no_warning_when_the_final_check_is_still_close():
    near = result(1, saved_at=1000, saved_validation=0.6, final_validation=0.4)
    assert collapse_warnings([near]) == []


# ---- the numbers behind it ----


def test_playthrough_stats_gives_steps_for_every_try_and_ratio_for_finished_ones(tmp_path):
    config = ConfigFile.model_validate(small_generated_config())
    pools = config.resolve_pools()
    run_dir = train(config, pools.train, run_dir=tmp_path / "run", pools=pools)
    stats = playthrough_stats(run_dir / "brain.onnx", pools.test)
    assert stats["avg_steps"] > 0
    assert stats["avg_path_ratio"] is None or stats["avg_path_ratio"] >= 1.0


def test_train_writes_test_stats_next_to_the_scores(tmp_path):
    config = ConfigFile.model_validate(small_generated_config())
    pools = config.resolve_pools()
    run_dir = train(config, pools.train, run_dir=tmp_path / "run", pools=pools)
    stats = json.loads((run_dir / "test_stats.json").read_text())
    assert set(stats) == {"avg_steps", "avg_path_ratio"}


def test_a_seed_result_carries_the_saved_try_and_the_final_check(tmp_path):
    config = ConfigFile.model_validate(small_generated_config())
    results = list(run_seeds(config, [1], 1, tmp_path, log_every=10, plot=False))
    one = results[0]
    assert one.saved_at is not None and one.saved_at % 10 == 0
    assert one.saved_validation is not None
    assert one.final_validation is not None
    assert one.test_steps is not None
    assert one.tries_done == 40  # the run did all 40 tries (it did not stop early)
