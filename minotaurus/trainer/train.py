"""Training loop: run MazeEnv episodes, call the method, log metrics, checkpoint, export."""

from __future__ import annotations

import json
import pickle
from datetime import datetime
from pathlib import Path

import torch

from minotaurus.engine import MazeEnv
from minotaurus.trainer.config import TrainConfig
from minotaurus.trainer.dqn import DQNAgent
from minotaurus.trainer.export import export_dqn, export_qtable
from minotaurus.trainer.qtable import QTableAgent

CHECKPOINT_EVERY = 500


def make_agent(config: TrainConfig) -> QTableAgent | DQNAgent:
    if config.method == "qtable":
        return QTableAgent(**config.params, seed=config.seed)
    return DQNAgent(**config.params, seed=config.seed)


def _checkpoint(agent, config: TrainConfig, folder: Path, episode: int) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    if config.method == "qtable":
        with open(folder / f"ep{episode:06d}.pkl", "wb") as fh:
            pickle.dump({k: v.tolist() for k, v in agent.q.items()}, fh)
    else:
        torch.save(agent.net.state_dict(), folder / f"ep{episode:06d}.pt")


def train(
    config: TrainConfig,
    runs_dir: str | Path = "runs",
    *,
    run_dir: str | Path | None = None,
    log_every: int = 10,
    progress=None,
) -> Path:
    """Train and export. Returns the run folder (metrics.jsonl, checkpoints/, config.json,
    brain.onnx). The same seed gives the same metrics."""
    if run_dir is None:
        run_dir = Path(runs_dir) / config.name / datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps(config.raw, indent=2) + "\n")

    agent = make_agent(config)
    envs = [MazeEnv(level, window=config.window) for level in config.levels]
    window_reward = window_steps = window_wins = window_loss = 0.0
    loss_count = 0
    with open(run_dir / "metrics.jsonl", "w") as metrics:
        for episode in range(1, config.episodes + 1):
            env = envs[(episode - 1) % len(envs)]
            obs, _ = env.reset(seed=config.seed + episode)
            total, steps, done = 0.0, 0, False
            while not done:
                action = agent.act(obs)
                nxt, reward, terminated, truncated, _ = env.step(action)
                # a step-limit cut is not a real end of the task: keep bootstrapping through it
                result = (
                    agent.step(obs, action, reward, nxt, terminated)
                    if isinstance(agent, DQNAgent)
                    else agent.update(obs, action, reward, nxt, terminated)
                )
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
                _checkpoint(agent, config, run_dir / "checkpoints", episode)

    ids = [level.id for level in config.levels]
    target = run_dir / "brain.onnx"
    if config.method == "qtable":
        export_qtable(agent, target, config.name, ids, config.window)
    else:
        export_dqn(agent, target, config.name, ids, config.window)
    return run_dir
