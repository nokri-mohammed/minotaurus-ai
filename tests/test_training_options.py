"""Training options: step limit, curriculum, best-on-validation export, recorded settings."""

import json

import pytest
from pydantic import ValidationError

from minotaurus.engine.levels import DEFAULT_STEP_LIMIT_FACTOR, load_level_by_id
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.train import stage_starts, train, training_copies
from tests.test_trainer import small_qtable_config


def random_walk_config(episodes: int = 3) -> dict:
    """A Q-table that only ever moves at random (epsilon stays at 1)."""
    data = small_qtable_config(episodes)
    data["qtable"]["epsilon_start"] = 1.0
    data["qtable"]["epsilon_end"] = 1.0
    data["qtable"]["epsilon_decay"] = 1.0
    return data


def read_lines(run_dir) -> list[dict]:
    rows = []
    for text in (run_dir / "metrics.jsonl").read_text().splitlines():
        rows.append(json.loads(text))
    return rows


# ---- training step limit ----


def test_train_step_limit_factor_is_unset_by_default():
    assert ConfigFile.model_validate(small_qtable_config()).train_step_limit_factor is None


@pytest.mark.parametrize("bad", [0, -1.0])
def test_train_step_limit_factor_must_be_positive(bad):
    data = small_qtable_config()
    data["train_step_limit_factor"] = bad
    with pytest.raises(ValidationError, match="train_step_limit_factor"):
        ConfigFile.model_validate(data)


def test_training_copies_change_only_the_step_limit():
    level = load_level_by_id("easy-01")  # shortest path 13 steps
    same = training_copies((level,), None)
    assert same == (level,)
    longer = training_copies((level,), 20.0)[0]
    assert longer.step_limit == 20 * 13
    assert (longer.id, longer.grid) == (level.id, level.grid)
    assert level.step_limit_factor == DEFAULT_STEP_LIMIT_FACTOR  # the original is untouched


def test_training_uses_the_training_step_limit(tmp_path):
    # factor 0.5 on easy-01: a limit of 6 steps, too few to reach an exit 13 steps away,
    # so every training episode lasts exactly 6 steps
    data = random_walk_config()
    data["train_step_limit_factor"] = 0.5
    config = ConfigFile.model_validate(data)
    run = train(config, config.resolve_levels(), run_dir=tmp_path / "r", log_every=3)
    assert read_lines(run)[0]["avg_steps"] == 6


def test_scoring_keeps_the_normal_step_limit(tmp_path):
    data = random_walk_config()
    data["train_step_limit_factor"] = 0.5
    data["levels"] = {
        "generated": {"size": 7, "maze_seed": 5, "train": 4, "validation": 2, "test": 2}
    }
    config = ConfigFile.model_validate(data)
    pools = config.resolve_pools()
    train(config, pools.train, run_dir=tmp_path / "r", log_every=3, pools=pools)
    for level in (*pools.train, *pools.validation, *pools.test):
        assert level.step_limit_factor == DEFAULT_STEP_LIMIT_FACTOR


# ---- size curriculum (experimental) ----


def curriculum_config(stages, episodes: int = 9) -> dict:
    data = random_walk_config(episodes)
    data["levels"] = {
        "generated": {"size": 9, "maze_seed": 1, "train": 6, "validation": 2, "test": 2}
    }
    data["stages"] = stages
    return data


def test_stages_are_unset_by_default():
    assert ConfigFile.model_validate(small_qtable_config()).stages is None


@pytest.mark.parametrize(
    "stages",
    [
        [5, 7],  # the last stage must be the pool size (9)
        [5, 8, 9],  # sizes are odd
        [3, 9],  # sizes are 5 to 41
        [9],  # one stage is no curriculum
    ],
)
def test_bad_stages_are_refused(stages):
    with pytest.raises(ValidationError, match="stages"):
        ConfigFile.model_validate(curriculum_config(stages))


def test_stages_need_generated_levels():
    data = small_qtable_config()
    data["stages"] = [5, 7]
    with pytest.raises(ValidationError, match="stages"):
        ConfigFile.model_validate(data)


def test_stage_starts_split_the_episodes_evenly():
    assert stage_starts(5000, 3) == [1, 1667, 3334]
    assert stage_starts(10, 3) == [1, 4, 7]
    assert stage_starts(10, 1) == [1]


def test_resolve_stages_gives_small_mazes_first_and_the_train_pool_last():
    config = ConfigFile.model_validate(curriculum_config([5, 7, 9]))
    pools = config.resolve_pools()
    stages = config.resolve_stages(pools)
    assert stages[-1] == pools.train
    assert {lv.width for lv in stages[0]} == {5}
    assert {lv.width for lv in stages[1]} == {7}
    assert len(stages[0]) == 2  # 5 x 5 has only 2 different mazes
    assert len(stages[1]) == 6  # up to the train pool size
    assert ConfigFile.model_validate(random_walk_config()).resolve_stages(None) is None


def test_training_plays_the_stages_in_order(tmp_path, monkeypatch):
    import minotaurus.trainer.train as train_module

    widths = []

    class SpyEnv(train_module.MazeEnv):
        def reset(self, *, seed=None, options=None):
            widths.append(self.level.width)
            return super().reset(seed=seed, options=options)

    monkeypatch.setattr(train_module, "MazeEnv", SpyEnv)
    config = ConfigFile.model_validate(curriculum_config([5, 7, 9], episodes=9))
    pools = config.resolve_pools()
    train(config, pools.train, run_dir=tmp_path / "r", stages=config.resolve_stages(pools))
    assert widths == [5, 5, 5, 7, 7, 7, 9, 9, 9]


# ---- best brain on validation (G4) ----


def g4_config(episodes: int = 6, eval_every: int | None = 2) -> ConfigFile:
    from tests.test_trainer import small_dqn_config

    data = small_dqn_config(episodes)
    data["levels"] = {
        "generated": {"size": 7, "maze_seed": 5, "train": 4, "validation": 2, "test": 2}
    }
    if eval_every is not None:
        data["eval_every"] = eval_every
    return ConfigFile.model_validate(data)


def scripted_validation(monkeypatch, values):
    """Replace the validation score with `values`, one per check, and remember the brain's
    scores on one fixed view at each check (to know which brain was exported)."""
    import numpy as np

    import minotaurus.trainer.train as train_module

    probe = np.zeros(77, dtype=np.float32)
    probe[0] = 1.0
    seen = []
    queue = list(values)

    def fake(agent, levels, window):
        seen.append(agent.scores(probe).copy())
        return queue.pop(0)

    monkeypatch.setattr(train_module, "validation_success", fake)
    return probe, seen


def validation_lines(run_dir) -> list[dict]:
    rows = []
    for row in read_lines(run_dir):
        if "validation_success" in row:
            rows.append(row)
    return rows


def test_eval_every_defaults_to_250_with_pools_and_is_off_without():
    with_pools = g4_config(eval_every=None)
    assert with_pools.eval_every is None
    assert with_pools.validation_interval(with_pools.resolve_pools()) == 250
    assert with_pools.validation_interval(None) == 0
    assert g4_config(eval_every=0).validation_interval(with_pools.resolve_pools()) == 0
    hand_made = ConfigFile.model_validate(small_qtable_config())
    assert hand_made.validation_interval(None) == 0


def test_eval_every_needs_generated_levels():
    data = small_qtable_config()
    data["eval_every"] = 100
    with pytest.raises(ValidationError, match="eval_every"):
        ConfigFile.model_validate(data)


def test_a_worse_last_brain_is_not_exported(tmp_path, monkeypatch):
    from minotaurus.brain import load_brain

    probe, seen = scripted_validation(monkeypatch, [0.5, 0.9, 0.2])  # checks at 2, 4 and 6
    config = g4_config()
    pools = config.resolve_pools()
    run = train(config, pools.train, run_dir=tmp_path / "r", log_every=2, pools=pools)
    brain = load_brain(run / "brain.onnx")
    assert brain.scores(probe) == pytest.approx(seen[1], abs=1e-5)  # the episode 4 brain
    assert not np_equal(seen[1], seen[2])  # the last brain really was a different one
    assert brain.meta["exported_episode"] == "4"
    checks = validation_lines(run)
    assert [row["episode"] for row in checks[:3]] == [2, 4, 6]
    assert checks[-1] == {"exported_episode": 4, "validation_success": 0.9}


def np_equal(a, b) -> bool:
    import numpy as np

    return bool(np.allclose(a, b, atol=1e-6))


def test_a_validation_tie_exports_the_later_brain(tmp_path, monkeypatch):
    scripted_validation(monkeypatch, [0.5, 0.5, 0.2])
    config = g4_config()
    pools = config.resolve_pools()
    run = train(config, pools.train, run_dir=tmp_path / "r", log_every=2, pools=pools)
    assert validation_lines(run)[-1]["exported_episode"] == 4


def test_all_zero_on_validation_exports_the_final_brain_with_a_warning(tmp_path, monkeypatch):
    scripted_validation(monkeypatch, [0.0, 0.0, 0.0])
    config = g4_config()
    pools = config.resolve_pools()
    run = train(config, pools.train, run_dir=tmp_path / "r", log_every=2, pools=pools)
    last = validation_lines(run)[-1]
    assert last["exported_episode"] == 6
    assert "0%" in last["warning"]


def test_the_final_episode_is_always_checked(tmp_path, monkeypatch):
    scripted_validation(monkeypatch, [0.1, 0.2, 0.3, 0.4])  # checks at 2, 4, 6 and 7
    config = g4_config(episodes=7)
    pools = config.resolve_pools()
    run = train(config, pools.train, run_dir=tmp_path / "r", log_every=2, pools=pools)
    assert validation_lines(run)[-1]["exported_episode"] == 7


def test_eval_every_0_exports_the_last_brain_as_before(tmp_path, monkeypatch):
    scripted_validation(monkeypatch, [])  # any check would fail: the list is empty
    config = g4_config(eval_every=0)
    pools = config.resolve_pools()
    run = train(config, pools.train, run_dir=tmp_path / "r", log_every=2, pools=pools)
    assert validation_lines(run) == []
    from minotaurus.brain import load_brain

    assert "exported_episode" not in load_brain(run / "brain.onnx").meta


def test_validation_success_plays_the_brain_without_random_moves():
    from minotaurus.trainer.qtable import QTableAgent
    from minotaurus.trainer.train import validation_success

    level = load_level_by_id("easy-01")
    agent = QTableAgent(0.1, 0.9, 1.0, 1.0, 1.0)  # epsilon 1: random while exploring
    # an empty table always picks move 0 (up) when not exploring: it never finishes
    assert validation_success(agent, (level,), 5) == 0.0


def test_cli_train_says_which_episode_was_exported(tmp_path):
    from typer.testing import CliRunner

    from minotaurus.cli import app

    data = small_qtable_config(episodes=4)
    data["levels"] = {
        "generated": {"size": 7, "maze_seed": 5, "train": 4, "validation": 2, "test": 2}
    }
    data["eval_every"] = 2
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data))
    result = CliRunner().invoke(
        app, ["train", "--config", str(path), "--runs-dir", str(tmp_path / "runs"), "--no-plot"]
    )
    assert result.exit_code == 0, result.output
    assert "exported the brain from episode" in result.output


# ---- every training option recorded (config.json and .onnx metadata) ----


def test_a_plain_run_records_the_options_at_their_defaults(tmp_path):
    from minotaurus.brain import load_brain

    config = ConfigFile.model_validate(small_qtable_config(episodes=2))
    run = train(config, config.resolve_levels(), run_dir=tmp_path / "r")
    saved = json.loads((run / "config.json").read_text())
    assert saved["train_step_limit_factor"] is None
    assert saved["stages"] is None
    assert saved["eval_every"] == 0  # no pools: no validation checks
    assert saved["policy_epsilon"] == 0.0
    assert ConfigFile.model_validate(saved).episodes == 2  # still a valid config file
    training = json.loads(load_brain(run / "brain.onnx").meta["training"])
    assert training == {
        "shaping": False,
        "shaping_on_bump": None,
        "novelty_bonus": None,
        "revisit_penalty": None,
        "train_step_limit_factor": None,
        "stages": None,
        "eval_every": 0,
        "policy_epsilon": 0.0,
        "wall_mask": False,
        "patience": None,
        "exported_episode": None,
        "stopped_at_episode": None,
    }


def test_a_research_run_records_every_option_and_the_chosen_episode(tmp_path):
    from minotaurus.brain import load_brain
    from tests.test_trainer import small_dqn_config

    data = small_dqn_config(episodes=4)
    data["levels"] = {
        "generated": {"size": 9, "maze_seed": 1, "train": 4, "validation": 2, "test": 2}
    }
    data["dqn"]["shaping"] = True
    data["dqn"]["shaping_on_bump"] = False
    data["train_step_limit_factor"] = 20.0
    data["stages"] = [7, 9]
    data["eval_every"] = 2
    data["policy_epsilon"] = 0.05
    config = ConfigFile.model_validate(data)
    pools = config.resolve_pools()
    run = train(
        config,
        pools.train,
        run_dir=tmp_path / "r",
        pools=pools,
        stages=config.resolve_stages(pools),
    )
    saved = json.loads((run / "config.json").read_text())
    assert saved["dqn"]["shaping"] is True and saved["dqn"]["shaping_on_bump"] is False
    assert saved["train_step_limit_factor"] == 20.0 and saved["stages"] == [7, 9]
    assert saved["eval_every"] == 2 and saved["policy_epsilon"] == 0.05
    meta = load_brain(run / "brain.onnx").meta
    training = json.loads(meta["training"])
    assert training["shaping"] is True and training["shaping_on_bump"] is False
    assert training["stages"] == [7, 9] and training["eval_every"] == 2
    assert training["exported_episode"] == int(meta["exported_episode"])


def test_eval_every_is_recorded_as_used(tmp_path):
    config = g4_config(episodes=2, eval_every=None)  # unset: 250 with pools
    pools = config.resolve_pools()
    run = train(config, pools.train, run_dir=tmp_path / "r", pools=pools)
    assert json.loads((run / "config.json").read_text())["eval_every"] == 250


def test_the_shaped_example_validates():
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "data" / "examples" / "dqn-shaped-brain.json"
    config = ConfigFile.model_validate_json(path.read_text())
    assert config.shaping and config.eval_every == 250
    assert config.levels.generated.size == 9
