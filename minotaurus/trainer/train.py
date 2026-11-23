"""Training loop: run MazeEnv episodes, call the method, log metrics, checkpoint, export."""

from __future__ import annotations

import copy
import json
import pickle
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import torch

from minotaurus.brain.onnx_brain import POLICY_EPSILON_KEY
from minotaurus.engine import MazeEnv
from minotaurus.engine.levels import Level
from minotaurus.engine.pools import Pools
from minotaurus.trainer import shaping
from minotaurus.trainer.config import ConfigFile
from minotaurus.trainer.dqn import DQNAgent
from minotaurus.trainer.evaluate import POOLS_KEY, score_brain
from minotaurus.trainer.export import export_dqn, export_qtable
from minotaurus.trainer.qtable import QTableAgent

CHECKPOINT_EVERY = 500
EXPORTED_EPISODE_KEY = "exported_episode"  # .onnx metadata: the episode of the exported brain


def make_agent(config: ConfigFile) -> QTableAgent | DQNAgent:
    if config.method == "qtable":
        return QTableAgent(**config.params, seed=config.seed)
    return DQNAgent(**config.params, seed=config.seed)


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


def validation_success(
    agent: QTableAgent | DQNAgent, levels: tuple[Level, ...], window: int
) -> float:
    """Share of `levels` the agent finishes when it plays its best move every step (no random
    moves), as the exported brain would. Example: 0.5 when it finishes 1 of 2 mazes."""
    finished = 0
    for level in levels:
        env = MazeEnv(level, window=window)
        obs, _ = env.reset()
        done = terminated = False
        while not done:
            obs, _, terminated, truncated, _ = env.step(agent.act(obs, explore=False))
            done = terminated or truncated
        if terminated:
            finished += 1
    return finished / len(levels)


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
        config.model_dump_json(indent=2, exclude_unset=True) + "\n"
    )

    agent = make_agent(config)
    # One stage (all of `levels`) unless a curriculum gives several.
    if stages is None:
        stages = [levels]
    stage_envs = []
    for stage in stages:
        envs = []
        for level in training_copies(stage, config.train_step_limit_factor):
            envs.append(MazeEnv(level, window=config.window))
        stage_envs.append(envs)
    starts = stage_starts(config.episodes, len(stage_envs))
    # Reward shaping (training only, off by default): phi for each training level, by level id.
    potentials = {}
    if config.shaping:
        for envs in stage_envs:
            for env in envs:
                potentials[env.level.id] = shaping.potential(env.level)
    stage = 0
    # Best brain on validation (G4): check every `interval` tries and at the end; 0 = off.
    interval = config.validation_interval(pools)
    best_success, best_episode, best_state = -1.0, 0, None
    window_reward = window_steps = window_wins = window_loss = 0.0
    loss_count = 0
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
            while not done:
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
                # a step-limit cut is not a real end of the task: keep bootstrapping through it
                if isinstance(agent, DQNAgent):
                    result = agent.step(obs, action, reward, nxt, terminated)
                else:
                    result = agent.update(obs, action, reward, nxt, terminated)
                if result is not None:
                    window_loss += result
                    loss_count += 1
                total += reward
                steps += 1
                obs = nxt
                done = terminated or truncated
            agent.end_episode()
            window_reward += total
            window_steps += steps
            window_wins += 1.0 if terminated else 0.0
            if episode % log_every == 0 or episode == config.episodes:
                n = log_every if episode % log_every == 0 else episode % log_every
                line = {
                    "episode": episode,
                    "avg_reward": round(window_reward / n, 5),
                    "avg_steps": round(window_steps / n, 3),
                    "success_rate": round(window_wins / n, 4),
                    "epsilon": round(agent.epsilon, 5),
                    "loss": round(window_loss / loss_count, 6) if loss_count else None,
                }
                metrics.write(json.dumps(line) + "\n")
                metrics.flush()
                if progress:
                    progress(line)
                window_reward = window_steps = window_wins = window_loss = 0.0
                loss_count = 0
            if episode % CHECKPOINT_EVERY == 0:
                _checkpoint(agent, run_dir / "checkpoints", episode)
            if interval and (episode % interval == 0 or episode == config.episodes):
                success = validation_success(agent, pools.validation, config.window)
                metrics.write(json.dumps({"episode": episode, "validation_success": success}))
                metrics.write("\n")
                metrics.flush()
                if success >= best_success:  # a tie keeps the later brain
                    best_success, best_episode = success, episode
                    best_state = _snapshot(agent)
        if interval:
            chosen = {"exported_episode": best_episode, "validation_success": best_success}
            if best_success == 0.0:
                # nothing finished a validation maze: keep the final brain (also the last checked)
                chosen["warning"] = "0% on validation at every check: exported the final brain"
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
    if isinstance(agent, QTableAgent):
        export_qtable(agent, target, config.name, ids, config.window, extra_meta)
    else:
        export_dqn(agent, target, config.name, ids, config.window, extra_meta)
    if pools is not None:
        scores = score_brain(target, config, pools)
        (run_dir / "scores.json").write_text(json.dumps(scores, indent=2) + "\n")
    return run_dir
