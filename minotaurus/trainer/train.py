"""Training loop: run MazeEnv episodes, call the method, log metrics, checkpoint, export."""

from __future__ import annotations

import copy
import json
import pickle
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import torch

from minotaurus.brain.onnx_brain import LOOP_ESCAPE_KEY, POLICY_EPSILON_KEY, WALL_MASK_KEY
from minotaurus.engine import MazeEnv
from minotaurus.engine.levels import Level, shortest_path_length
from minotaurus.engine.loops import LOOP_REPEATS, LoopWatch
from minotaurus.engine.observe import obs_size
from minotaurus.engine.pools import Pools
from minotaurus.trainer import shaping
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.dqn import DQNAgent
from minotaurus.trainer.evaluate import (
    POOLS_KEY,
    playthrough_stats,
    score_brain,
    score_fixed_levels,
)
from minotaurus.trainer.export import (
    PARAMETERS_KEY,
    export_dqn,
    export_qtable,
    parameter_count,
)
from minotaurus.trainer.qtable import QTableAgent
from minotaurus.trainer.teacher import Teacher

CHECKPOINT_EVERY = 500
TRAINING_KEY = "training"  # .onnx metadata: every training option, as JSON
EXPORTED_EPISODE_KEY = "exported_episode"  # .onnx metadata: the episode of the exported brain


def make_agent(config: ConfigFile) -> QTableAgent | DQNAgent:
    if config.method == "qtable":
        return QTableAgent(**config.params, seed=config.seed, wall_mask=config.wall_mask)
    return DQNAgent(
        **config.params,
        seed=config.seed,
        wall_mask=config.wall_mask,
        obs_len=obs_size(config.window, config.obs_version),
    )


def _checkpoint(agent: QTableAgent | DQNAgent, folder: Path, episode: int) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    if isinstance(agent, QTableAgent):
        table = {}
        for key, row in agent.q.items():
            table[key] = row.tolist()
        with open(folder / f"ep{episode:06d}.pkl", "wb") as fh:
            pickle.dump(table, fh)
    else:
        torch.save(agent.net.state_dict(), folder / f"ep{episode:06d}.pt")


def training_copies(
    levels: tuple[Level, ...], step_limit_factor: float | None
) -> tuple[Level, ...]:
    """The levels as training plays them: with `step_limit_factor` when it is set.

    These are copies; the levels passed in (and the pools that scoring uses) keep their own factor.
    Example: easy-01 (shortest path 13) with factor 20 -> a step limit of 260 in training.
    """
    if step_limit_factor is None:
        return levels
    copies = []
    for level in levels:
        copies.append(replace(level, step_limit_factor=step_limit_factor))
    return tuple(copies)


def _recorded_config(config: ConfigFile, pools: Pools | None) -> dict:
    """config.json: the settings as written, plus every training option as this run uses it.

    The result is still a valid config file, so the run can be repeated from it.
    """
    data = json.loads(config.model_dump_json(exclude_unset=True))
    options = config.training_options(pools)
    if config.method == "dqn":
        data["dqn"]["shaping"] = options["shaping"]
        data["dqn"]["shaping_on_bump"] = options["shaping_on_bump"]
    for key in ("train_step_limit_factor", "stages", "eval_every", "policy_epsilon"):
        data[key] = options[key]
    return data


def validation_check(
    agent: QTableAgent | DQNAgent, levels: tuple[Level, ...], window: int, obs_version: int = 1
) -> tuple[float, int]:
    """Play `levels` with the agent's best move every step (no random moves), as the exported
    brain would. Returns (share finished, how many mazes it looped on without finishing).

    A loop is the same square seen with the same input for the third time. Example: (0.5, 1) when
    it finishes 1 of 2 mazes and loops on the other.
    """
    finished = 0
    loops = 0
    for level in levels:
        env = MazeEnv(level, window=window, obs_version=obs_version)
        obs, _ = env.reset()
        watch = LoopWatch()
        looped = False
        done = terminated = False
        while not done:
            obs, _, terminated, truncated, _ = env.step(agent.act(obs, explore=False))
            if watch.see(env.pos, obs) >= LOOP_REPEATS:
                looped = True
            done = terminated or truncated
        if terminated:
            finished += 1
        elif looped:
            loops += 1
    return finished / len(levels), loops


def validation_success(
    agent: QTableAgent | DQNAgent, levels: tuple[Level, ...], window: int, obs_version: int = 1
) -> float:
    """Share of `levels` the agent finishes when it plays its best move every step (no random
    moves), as the exported brain would. Example: 0.5 when it finishes 1 of 2 mazes."""
    return validation_check(agent, levels, window, obs_version)[0]


def _snapshot(agent: QTableAgent | DQNAgent):
    """A copy of what the agent has learned (the network weights or the table)."""
    if isinstance(agent, DQNAgent):
        return copy.deepcopy(agent.net.state_dict())
    table = {}
    for key, row in agent.q.items():
        table[key] = row.copy()
    return table


def _restore(agent: QTableAgent | DQNAgent, state) -> None:
    if isinstance(agent, DQNAgent):
        agent.net.load_state_dict(state)
    else:
        agent.q = state


def stage_starts(episodes: int, n_stages: int) -> list[int]:
    """The first episode (counting from 1) of each stage when `episodes` are split evenly.

    Example: stage_starts(5000, 3) -> [1, 1667, 3334].
    """
    starts = []
    for index in range(n_stages):
        starts.append(1 + index * episodes // n_stages)
    return starts


def train(
    config: ConfigFile,
    levels: tuple[Level, ...],
    runs_dir: str | Path = "runs",
    *,
    run_dir: str | Path | None = None,
    log_every: int = 10,
    progress=None,
    pools: Pools | None = None,
    stages: list[tuple[Level, ...]] | None = None,
) -> Path:
    """Train on `levels` (from config.resolve_levels()) and export. Returns the run folder
    (metrics.jsonl, checkpoints/, config.json, brain.onnx). The same seed gives the same metrics.
    With `pools` (from config.resolve_pools()) the exported brain also gets scores.json: its
    success rate on the train, validation and test mazes. With `stages` (from
    config.resolve_stages(pools)) the episodes are split evenly over those level sets, in order."""
    if run_dir is None:
        run_dir = Path(runs_dir) / config.name / datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(
        json.dumps(_recorded_config(config, pools), indent=2) + "\n"
    )

    agent = make_agent(config)
    # One stage (all of `levels`) unless a curriculum gives several.
    if stages is None:
        stages = [levels]
    stage_envs = []
    for stage in stages:
        envs = []
        for level in training_copies(stage, config.train_step_limit_factor):
            envs.append(MazeEnv(level, window=config.window, obs_version=config.obs_version))
        stage_envs.append(envs)
    starts = stage_starts(config.episodes, len(stage_envs))
    # Reward shaping (training only, off by default): phi for each training level, by level id.
    potentials = {}
    if config.shaping:
        for envs in stage_envs:
            for env in envs:
                potentials[env.level.id] = shaping.potential(env.level)
    # Novelty bonus and revisit penalty (training only, DQN, 0 = off).
    novelty_bonus = 0.0
    revisit_penalty = 0.0
    if config.method == "dqn":
        novelty_bonus = config.dqn.novelty_bonus
        revisit_penalty = config.dqn.revisit_penalty
    visit_rewards = novelty_bonus > 0.0 or revisit_penalty > 0.0
    # Loop stop (training only): end a try that goes in circles, with a penalty.
    loop_stop = config.loop_stop
    # Imitation (training only, DQN): a teacher for the first tries.
    imitation = config.imitation
    teachers = {}
    if imitation is not None:
        for envs in stage_envs:
            for env in envs:
                teachers[env.level.id] = Teacher(env.level)
    stage = 0
    # Best brain on validation (G4): check every `interval` tries and at the end; 0 = off.
    interval = config.validation_interval(pools)
    best_success, best_episode, best_state = -1.0, 0, None
    best_loops = 10**9  # loops of the best brain so far: on a tied score, fewer loops wins
    checks_without_gain = 0  # validation checks in a row without a better score (early stop)
    stopped_at = None  # the try training stopped at, when it stopped early
    window_reward = window_steps = window_wins = window_loss = 0.0
    loss_count = 0
    window_ratio = 0.0  # sum of steps / shortest path over the finished tries of this window
    window_loops = 0  # tries of this window that loop stop ended
    shortest = {}  # level id -> shortest path length, worked out once per level
    with open(run_dir / "metrics.jsonl", "w") as metrics:
        for episode in range(1, config.episodes + 1):
            if stage + 1 < len(starts) and episode >= starts[stage + 1]:
                stage += 1
            envs = stage_envs[stage]
            env = envs[(episode - starts[stage]) % len(envs)]
            obs, _ = env.reset(seed=config.seed + episode)
            phi = potentials.get(env.level.id)
            total, steps, done = 0.0, 0, False
            terminated = False  # set by every step; defined here so it exists after the loop
            watch = LoopWatch()
            looped = False
            teacher = None
            teacher_share = 0.0
            if imitation is not None and episode <= imitation.episodes:
                teacher = teachers[env.level.id]
                # from teacher_share down to 0 in a straight line over the imitation tries
                left = 1.0 - (episode - 1) / imitation.episodes
                teacher_share = imitation.teacher_share * left
            while not done:
                taught_action = None
                if teacher is not None:
                    taught_action = teacher.move(env.pos)
                if taught_action is not None and agent.rng.random() < teacher_share:
                    action = taught_action
                else:
                    action = agent.act(obs)
                before = env.pos
                nxt, reward, terminated, truncated, _ = env.step(action)
                if phi is not None:
                    reward = shaping.shaped_reward(
                        reward,
                        phi,
                        before,
                        env.pos,
                        gamma=config.dqn.gamma,
                        on_bump=config.dqn.shaping_on_bump,
                    )
                if visit_rewards:
                    # training only: novelty bonus / revisit penalty from the visit counts
                    reward += shaping.visit_reward(
                        shaping.visits_before(env), novelty_bonus, revisit_penalty
                    )
                running = not terminated and not truncated
                # same square, same input, for the `repeats`-th time: end the try, with a penalty
                if (
                    loop_stop is not None
                    and running
                    and watch.see(env.pos, nxt) >= loop_stop.repeats
                ):
                    reward -= loop_stop.penalty
                    looped = True
                # a step-limit cut is not a real end of the task: keep bootstrapping through it
                if isinstance(agent, DQNAgent):
                    result = agent.step(obs, action, reward, nxt, terminated)
                else:
                    result = agent.update(obs, action, reward, nxt, terminated)
                if result is not None:
                    window_loss += result
                    loss_count += 1
                if taught_action is not None:
                    agent.imitate(obs, taught_action, imitation.margin, imitation.weight)
                total += reward
                steps += 1
                obs = nxt
                done = terminated or truncated or looped
            if looped:
                window_loops += 1
            agent.end_episode()
            window_reward += total
            window_steps += steps
            window_wins += 1.0 if terminated else 0.0
            if terminated:
                if env.level.id not in shortest:
                    shortest[env.level.id] = shortest_path_length(env.level)
                window_ratio += steps / shortest[env.level.id]
            if episode % log_every == 0 or episode == config.episodes:
                n = log_every if episode % log_every == 0 else episode % log_every
                line = {
                    "episode": episode,
                    "avg_reward": round(window_reward / n, 5),
                    "avg_steps": round(window_steps / n, 3),
                    "success_rate": round(window_wins / n, 4),
                    # steps / shortest path on the finished tries only; None if none finished
                    "avg_path_ratio": (
                        round(window_ratio / window_wins, 3) if window_wins > 0 else None
                    ),
                    "epsilon": round(agent.epsilon, 5),
                    "loss": round(window_loss / loss_count, 6) if loss_count else None,
                    "parameters": parameter_count(agent),
                }
                if loop_stop is not None:
                    line["loop_stops"] = window_loops
                metrics.write(json.dumps(line) + "\n")
                metrics.flush()
                if progress:
                    progress(line)
                window_reward = window_steps = window_wins = window_loss = 0.0
                loss_count = 0
                window_ratio = 0.0
                window_loops = 0
            if episode % CHECKPOINT_EVERY == 0:
                _checkpoint(agent, run_dir / "checkpoints", episode)
            if interval and (episode % interval == 0 or episode == config.episodes):
                success, loops = validation_check(
                    agent, pools.validation, config.window, config.obs_version
                )
                row = {"episode": episode, "validation_success": success, "validation_loops": loops}
                metrics.write(json.dumps(row))
                metrics.write("\n")
                metrics.flush()
                # Better: a higher score, or the same score with fewer loops (a tie is not better).
                gain = success > best_success or (success == best_success and loops < best_loops)
                if gain:
                    checks_without_gain = 0
                else:
                    checks_without_gain += 1
                # A tie in score and loops keeps the later brain; more loops on a tie keeps the old one.
                if success > best_success or (success == best_success and loops <= best_loops):
                    best_success, best_episode, best_loops = success, episode, loops
                    best_state = _snapshot(agent)
                if config.patience is not None and checks_without_gain >= config.patience:
                    stopped_at = episode  # early stop: no better check in `patience` checks
                    break
        if interval:
            chosen = {
                "exported_episode": best_episode,
                "validation_success": best_success,
                "validation_loops": best_loops,
            }
            if stopped_at is not None:
                chosen["stopped_at_episode"] = stopped_at
            if best_success == 0.0:
                # nothing finished a validation maze: keep the final brain (also the last checked)
                chosen["warning"] = (
                    "0% on validation at every check: exported the brain that looped least"
                )
            _restore(agent, best_state)
            metrics.write(json.dumps(chosen) + "\n")

    ids = []
    for level in levels:
        ids.append(level.id)
    target = run_dir / "brain.onnx"
    extra_meta = {}
    pool_settings = config.pool_settings()
    if pool_settings is not None:
        extra_meta[POOLS_KEY] = json.dumps(pool_settings, sort_keys=True)
    if interval:
        extra_meta[EXPORTED_EPISODE_KEY] = str(best_episode)
    if config.policy_epsilon > 0.0:
        extra_meta[POLICY_EPSILON_KEY] = str(config.policy_epsilon)
    if config.wall_mask:
        extra_meta[WALL_MASK_KEY] = "true"
    if config.loop_escape:
        extra_meta[LOOP_ESCAPE_KEY] = "true"
    training = config.training_options(pools)
    training["exported_episode"] = best_episode if interval else None
    training["stopped_at_episode"] = stopped_at
    extra_meta[TRAINING_KEY] = json.dumps(training)
    extra_meta[PARAMETERS_KEY] = str(parameter_count(agent))
    if isinstance(agent, QTableAgent):
        export_qtable(
            agent, target, config.name, ids, config.window, extra_meta, config.obs_version
        )
    else:
        export_dqn(agent, target, config.name, ids, config.window, extra_meta, config.obs_version)
    if pools is not None:
        scores = score_brain(target, config, pools)
        (run_dir / "scores.json").write_text(json.dumps(scores, indent=2) + "\n")
        fixed = score_fixed_levels(target)
        (run_dir / "fixed_levels.json").write_text(json.dumps(fixed, indent=2) + "\n")
        stats = playthrough_stats(target, pools.test)
        (run_dir / "test_stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    return run_dir
