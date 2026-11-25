"""Against loops (T1): loop watch, loop escape, loop stop, loop-aware choice, imitation, obs v2."""

import json

import numpy as np
import pytest
from pydantic import ValidationError

import minotaurus.trainer.train as train_module
from minotaurus.brain import BrainError, load_brain, obs_version_of, player
from minotaurus.engine import MazeEnv
from minotaurus.engine.env import DOWN, LEFT, RIGHT
from minotaurus.engine.loops import LOOP_REPEATS, LoopWatch
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.dqn import DQNAgent
from minotaurus.trainer.export import export_dqn, export_qtable
from minotaurus.trainer.multi import SeedResult, pick_best, results_table
from minotaurus.trainer.qtable import QTableAgent, obs_key
from minotaurus.trainer.teacher import Teacher
from minotaurus.trainer.train import train, validation_check
from tests.test_trainer import make_model, small_dqn_config, small_qtable_config

from .conftest import make_level

ROOM = ["#####", "#S..#", "#...#", "#..E#", "#####"]


def generated_dqn(episodes=8, **extra) -> dict:
    data = small_dqn_config(episodes)
    data["levels"] = {
        "generated": {"size": 7, "maze_seed": 5, "train": 4, "validation": 2, "test": 2}
    }
    data["eval_every"] = 2
    data.update(extra)
    return data


# ---- loop watch ----


def test_the_loop_watch_counts_the_same_state_again_and_again():
    watch = LoopWatch()
    obs = np.zeros(77, dtype=np.float32)
    assert watch.see((1, 1), obs) == 1
    assert watch.see((1, 1), obs) == 2
    assert watch.see((1, 2), obs) == 1  # another square is another state
    other = obs.copy()
    other[0] = 1.0
    assert watch.see((1, 1), other) == 1  # another input is another state
    assert LOOP_REPEATS == 3


# ---- loop escape (play) ----


def walk(mover, steps=40, obs_version=1):
    """Play `mover` on the room and return the squares the dot stood on."""
    env = MazeEnv(make_level(ROOM), obs_version=obs_version)
    obs, _ = env.reset()
    squares = []
    for _ in range(steps):
        obs, _, done, truncated, _ = env.step(mover(obs))
        squares.append(env.pos)
        if done or truncated:
            break
    return squares


def push_left(obs):
    return LEFT  # a wall at the start: it bumps for ever


def test_a_brain_that_bumps_for_ever_never_leaves_without_loop_escape():
    squares = walk(player(push_left, seed="a", loop_escape=False))
    assert set(squares) == {(1, 1)}


def test_loop_escape_makes_a_random_free_move_in_a_loop_and_the_run_repeats():
    first = walk(player(push_left, seed="a", loop_escape=True))
    again = walk(player(push_left, seed="a", loop_escape=True))
    assert set(first) != {(1, 1)}  # it got out of the corner
    assert first == again  # seeded: the same run twice


def test_loop_escape_leaves_a_brain_that_does_not_loop_alone():
    path = [RIGHT, RIGHT, DOWN, DOWN]
    moves = iter(path)

    def straight(obs):
        return next(moves)

    squares = walk(player(straight, seed="a", loop_escape=True), steps=4)
    assert squares == [(2, 1), (3, 1), (3, 2), (3, 3)]


def test_the_player_carries_the_obs_version():
    assert obs_version_of(push_left) == 1
    mover = player(push_left, seed="a", loop_escape=True)
    assert obs_version_of(mover) == 1


# ---- the loader ----


def test_the_loader_reads_loop_escape_and_refuses_a_bad_value(tmp_path):
    import onnx

    path = make_model(tmp_path)
    model = onnx.load(str(path))
    entry = model.metadata_props.add()
    entry.key, entry.value = "loop_escape", "true"
    onnx.save(model, str(path))
    assert load_brain(path).loop_escape is True
    model.metadata_props[-1].value = "yes"
    onnx.save(model, str(path))
    with pytest.raises(BrainError, match="loop_escape"):
        load_brain(path)


def test_the_loader_takes_a_version_2_brain_with_82_inputs_and_checks_the_size(tmp_path):
    brain = load_brain(make_model(tmp_path, in_shape=(1, 82), version="2"))
    assert brain.obs_version == 2 and brain.obs_len == 82
    assert brain(np.zeros(82, dtype=np.float32)) in range(4)
    with pytest.raises(BrainError, match="input"):
        load_brain(make_model(tmp_path, in_shape=(1, 77), version="2", name="b.onnx"))
    with pytest.raises(BrainError, match="input"):
        load_brain(make_model(tmp_path, in_shape=(1, 82), version="1", name="c.onnx"))


# ---- exports with obs_version 2 ----


def test_a_dqn_with_82_inputs_exports_and_the_brain_matches_the_agent(tmp_path):
    agent = DQNAgent([16], 0.01, 8, 0.9, 100, 10, 1.0, 0.05, 0.9, obs_len=82)
    export_dqn(agent, tmp_path / "d.onnx", "d", ["easy-01"], obs_version=2)
    brain = load_brain(tmp_path / "d.onnx")
    assert brain.obs_version == 2
    obs = np.random.default_rng(1).random(82).astype(np.float32)
    assert brain.scores(obs) == pytest.approx(agent.scores(obs), abs=1e-5)


def test_a_qtable_with_82_inputs_exports_the_same_rows_as_the_table(tmp_path):
    env = MazeEnv(make_level(ROOM), obs_version=2)
    agent = QTableAgent(0.5, 0.9, 1.0, 0.1, 0.99)
    obs, _ = env.reset()
    for action in (RIGHT, DOWN, LEFT):
        nxt, reward, *_ = env.step(action)
        agent.update(obs, action, reward, nxt, False)
        obs = nxt
    export_qtable(agent, tmp_path / "q.onnx", "q", ["t-01"], obs_version=2)
    brain = load_brain(tmp_path / "q.onnx")
    assert brain.obs_version == 2
    assert brain.scores(obs) == pytest.approx(agent.scores(obs), abs=1e-6)
    # the last move is part of the key: the same square after another move is another row
    env.reset()
    first, *_ = env.step(RIGHT)
    env.reset()
    env.step(DOWN)
    env.step(LEFT)  # back at the start but arrived by a different move
    assert obs_key(first) != obs_key(env._obs())


# ---- config ----


def test_the_new_settings_are_checked():
    base = generated_dqn()
    for bad in (
        {"observation": {"version": 3}},
        {"loop_stop": {"repeats": 1}},
        {"loop_stop": {"penalty": -1}},
    ):
        with pytest.raises(ValidationError):
            ConfigFile.model_validate({**base, **bad})
    data = generated_dqn(episodes=8)
    data["dqn"]["imitation"] = {"episodes": 9}
    with pytest.raises(ValidationError, match="imitation"):
        ConfigFile.model_validate(data)
    data["dqn"]["imitation"] = {"episodes": 4, "teacher_share": 0.5}
    config = ConfigFile.model_validate(data)
    assert config.imitation.margin == 0.8
    assert "imitation" not in config.params  # the agent never sees it


def test_a_qtable_config_has_no_imitation():
    assert ConfigFile.model_validate(small_qtable_config()).imitation is None


# ---- teacher and imitation ----


def test_the_teacher_steps_to_the_neighbour_nearest_the_exit(corridor):
    teacher = Teacher(corridor)
    assert teacher.move((1, 1)) == RIGHT
    room = Teacher(make_level(ROOM))
    assert room.move((3, 2)) == DOWN


def test_imitation_pulls_the_scores_towards_the_teachers_move():
    level = make_level(ROOM)
    teacher = Teacher(level)
    agent = DQNAgent([32], 0.01, 8, 0.9, 1000, 100, 0.0, 0.0, 1.0, wall_mask=True)
    env = MazeEnv(level)
    pairs = []
    for square in ((1, 1), (2, 1), (3, 1), (1, 2), (2, 2), (3, 2), (1, 3), (2, 3)):
        env.pos = square
        env.visits = {square: 1}
        pairs.append((env._obs(), teacher.move(square)))
    for _ in range(60):
        for obs, label in pairs:
            agent.imitate(obs, label, margin=0.8, weight=1.0)
    right = 0
    for obs, label in pairs:
        if agent.act(obs, explore=False) == label:
            right += 1
    assert right == len(pairs)


# ---- training ----


def test_validation_check_counts_the_mazes_a_brain_loops_on():
    class Pusher:
        def act(self, obs, explore=True):
            return LEFT  # into the wall at the start, for ever

    levels = (make_level(ROOM),)
    success, loops = validation_check(Pusher(), levels, 5)
    assert (success, loops) == (0.0, 1)
    assert validation_success_of(Pusher(), levels) == 0.0


def validation_success_of(agent, levels):
    return train_module.validation_success(agent, levels, 5)


def scripted_checks(monkeypatch, pairs):
    calls = []

    def fake(agent, levels, window, obs_version=1):
        calls.append(1)
        return pairs[min(len(calls), len(pairs)) - 1]

    monkeypatch.setattr(train_module, "validation_check", fake)


def exported_episode(tmp_path, monkeypatch, pairs):
    scripted_checks(monkeypatch, pairs)
    config = ConfigFile.model_validate(generated_dqn(episodes=6))
    pools = config.resolve_pools()
    run = train(config, pools.train, run_dir=tmp_path / "r", log_every=2, pools=pools)
    chosen = json.loads((run / "metrics.jsonl").read_text().splitlines()[-1])
    return chosen


def test_on_a_tied_score_the_brain_with_fewer_loops_is_saved(tmp_path, monkeypatch):
    chosen = exported_episode(tmp_path, monkeypatch, [(0.5, 3), (0.5, 1), (0.5, 2)])
    assert chosen["exported_episode"] == 4 and chosen["validation_loops"] == 1


def test_on_a_full_tie_the_later_brain_is_kept(tmp_path, monkeypatch):
    chosen = exported_episode(tmp_path, monkeypatch, [(0.5, 1), (0.5, 1), (0.5, 1)])
    assert chosen["exported_episode"] == 6


def test_a_better_score_beats_fewer_loops(tmp_path, monkeypatch):
    chosen = exported_episode(tmp_path, monkeypatch, [(0.5, 0), (0.9, 5), (0.5, 0)])
    assert chosen["exported_episode"] == 4


def test_a_run_with_every_option_trains_and_exports_a_version_2_brain(tmp_path):
    data = generated_dqn(
        episodes=8,
        observation={"version": 2},
        loop_stop={"repeats": 3, "penalty": 0.5},
        loop_escape=True,
        wall_mask=True,
    )
    data["dqn"]["imitation"] = {"episodes": 4, "teacher_share": 0.5}
    config = ConfigFile.model_validate(data)
    pools = config.resolve_pools()
    run = train(config, pools.train, run_dir=tmp_path / "r", log_every=2, pools=pools)
    brain = load_brain(run / "brain.onnx")
    assert brain.obs_version == 2 and brain.obs_len == 82
    assert brain.loop_escape is True and brain.wall_mask is True
    rows = []
    for text in (run / "metrics.jsonl").read_text().splitlines():
        rows.append(json.loads(text))
    assert "loop_stops" in rows[0]
    quiz = [row for row in rows if "validation_loops" in row]
    assert len(quiz) >= 3
    training = json.loads(brain.meta["training"])
    assert training["obs_version"] == 2
    assert training["loop_stop"] == {"repeats": 3, "penalty": 0.5}
    assert training["imitation"]["episodes"] == 4
    saved = json.loads((run / "config.json").read_text())
    assert ConfigFile.model_validate(saved).obs_version == 2  # still a valid config
    assert (run / "scores.json").exists()  # scoring played the version 2 brain


def test_a_plain_run_is_still_version_1_with_no_loop_keys(tmp_path):
    config = ConfigFile.model_validate(generated_dqn(episodes=4))
    pools = config.resolve_pools()
    run = train(config, pools.train, run_dir=tmp_path / "r", log_every=2, pools=pools)
    brain = load_brain(run / "brain.onnx")
    assert brain.obs_version == 1 and brain.loop_escape is False
    assert "loop_escape" not in brain.meta
    first = json.loads((run / "metrics.jsonl").read_text().splitlines()[0])
    assert "loop_stops" not in first


# ---- choosing a seed, and the table ----


def seed_result(seed, validation, loops, steps=10.0) -> SeedResult:
    return SeedResult(
        seed=seed,
        run_dir=f"seed-{seed}",
        seconds=1.0,
        success_rate=0.5,
        avg_steps=steps,
        avg_path_ratio=1.0,
        scores={"train": 0.5, "validation": validation, "test": 0.5},
        saved_loops=loops,
    )


def test_among_the_same_score_the_seed_with_fewer_loops_wins():
    results = [seed_result(1, 0.80, 7), seed_result(2, 0.80, 2), seed_result(3, 0.80, 5)]
    assert pick_best(results).seed == 2


def test_a_clearly_better_score_still_wins_over_fewer_loops():
    results = [seed_result(1, 0.70, 0), seed_result(2, 0.90, 9)]
    assert pick_best(results).seed == 2


def test_the_table_has_a_loops_column():
    results = [seed_result(1, 0.8, 4), seed_result(2, 0.8, 1)]
    lines = results_table(results, pick_best(results))
    assert "loops" in lines[0]
    assert lines[1].split()[3] == "4"


# ---- the arena plays a version 2 brain with a version 2 input ----


def test_the_arena_gives_a_version_2_brain_its_82_numbers():
    import asyncio

    from minotaurus.server.arena import run_arena

    seen = []

    def memory_brain(obs):
        seen.append(obs.shape)
        return RIGHT

    memory_brain.obs_version = 2

    async def run():
        messages = []
        async for message in run_arena(make_level(ROOM), memory_brain, 0.0, stuck_steps=5):
            messages.append(message)
        return messages

    asyncio.run(run())
    assert seen and set(seen) == {(82,)}


def test_the_no_loops_example_is_a_valid_config_with_every_option_on():
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "data" / "examples" / "dqn-no-loops-brain.json"
    config = ConfigFile.model_validate_json(path.read_text())
    assert config.obs_version == 2
    assert config.loop_stop is not None and config.loop_escape is True
    assert config.imitation is not None and config.imitation.episodes <= config.episodes
