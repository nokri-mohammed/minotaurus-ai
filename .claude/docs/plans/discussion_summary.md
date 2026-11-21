# minotaurus-ai: discussion summary

*   **Author:** nokri-mohammed
*   **Date:** 2026-11-20
*   **Source:** chief of staff and CEO chat, 2026-11-19 to 2026-11-20

## Problem

The CEO wants to learn how reinforcement learning (RL) works by doing it the way it is done for real:
a training script runs as a process on a machine, produces a model file, and that file is then loaded
into a game where you watch the trained agent play. A tutorial in the browser that trains live is not
enough; the point is to see the full process.

## The game

*   A simple 2D maze. The agent is a dot that must reach the exit.
*   **Race mode (gamification):** two players each enter an avatar name and load their own trained
    "brain" file. They pick one maze (or a random one). Both dots start on the same square and move
    one step per tick at the same time. First to the exit wins; same tick is a draw; a step limit
    (about 4x the shortest path) makes a wandering dot lose. Fading trails, step counters, a speed
    slider, replay, and a win scoreboard per name saved in the browser.

## Training

*   Each person trains their own brain on their own machine (CPU), with their own settings, then
    brings the file to the race.
*   One training script, `train.py --config my-brain.json`. The config chooses:
    *   `method`: `qtable` or `dqn` (neural network, Deep Q-Network);
    *   name, maze (a fixed maze or random mazes), episodes;
    *   DQN settings: layers, learning rate, batch size, gamma, epsilon decay, replay buffer, target
        network update;
    *   Q-table settings: learning rate, gamma, epsilon decay.
*   Config is JSON (not YAML), checked against a JSON Schema so bad settings give a clear error.
*   Training writes metrics and checkpoints during the run and a final model file.
*   Both methods export the same file format: **ONNX** (`.onnx`). A Q-table can be expressed as a
    single-layer ONNX model. The race page loads either kind the same way (ONNX Runtime Web).

## Stack

*   Training: **Python** (PyTorch, Gymnasium, NumPy, ONNX export). Chosen over Rust (burn) because
    the Python stack is the standard for RL and ML, has far more examples, exports ONNX in one call,
    and is the same toolchain as later LoRA fine-tuning work. Rust would use less memory.
*   Player and race page: **TypeScript with Bun**, ONNX Runtime Web in the browser.
*   Later: long training runs in a Docker container with a memory cap on the CEO's homelab server
    (done by homelab-it, with the CEO's go).

## Architecture decision (CEO, 2026-11-20)

*   **The rules live in one place: a game server.** The game engine (maze rules, moves, rewards,
    win, and how the maze is turned into numbers) exists once, on the server. The CEO wants this so
    the design scales to more complex games (for example the living-village world), where keeping
    two copies of the rules in step would be impossible.
*   **The interface is TypeScript/JavaScript in the browser.** It only draws what the server sends and
    sends player input (names, brain files, maze choice, start).
*   **Browser and server talk over a socket** (WebSocket).
*   Applications: engine plus game server, CLI trainer, browser interface.
*   **Chosen design ("go, this design", 2026-11-20):** the engine is Python and implements the
    Gymnasium interface (`reset()`, `step(action)`). The trainer imports the engine directly (full
    speed, no socket). The game server is a thin WebSocket wrapper around the same engine; it loads
    both players' `.onnx` brains and moves the dots, so the browser only draws. A future game written
    in another language gets a `RemoteEnv` class that speaks `reset` and `step` over a socket; the
    trainer does not change.

## Alternatives weighed

*   **Train in the browser (TypeScript):** rejected by author: the CEO wants to see a real training
    process run as a script on a machine or server, not an in-page demo.
*   **Rust with burn for training:** rejected by author: less mature, fewer examples, no gain for
    learning; memory saving not needed at this size.
*   **Go or Bun for training:** rejected by author: weak neural-network libraries.
*   **Two copies of the rules (Python for training, TypeScript in the page) checked by shared test
    cases:** rejected by author: rules must live in one place so the design scales to complex games.
*   **A full game engine with an RL toolkit (Godot RL Agents, Unity ML-Agents):** not chosen: heavy,
    hides the internals the CEO wants to learn.
*   **YAML config:** rejected by author: JSON needs no extra library and the player form can write it.
*   **Neural network only (no Q-table):** rejected by author: the trainer must offer both, chosen per
    config, so players can compare methods.

## Learning path (stages, one at a time on the CEO's word)

1.  Maze format, environment, training with both methods, ONNX export, a way to watch one brain play.
2.  Race page for two players.
3.  Dashboard: reward and success curves, checkpoint replays (clueless, improving, solved).
4.  Random mazes; test on mazes the brain has never seen.
5.  Long runs in Docker on the server.
6.  Harder: bigger mazes, CNN, traps and keys; maybe a second method (PPO).

## Known facts from the discussion

*   A Q-table knows only the positions it has seen, so a Q-table brain cannot solve a new maze; a
    neural network can learn patterns and generalise. The race on a random maze shows the difference.
*   Small mazes and small networks train on a CPU in minutes to hours; a GPU is only needed for much
    larger networks.

## Not decided yet

*   Public or private repo, and where the project lives (not created yet; the CEO said "do not create
    anything yet").
*   How a maze is turned into numbers for the brain (full grid, local view around the dot, or
    position only), and whether both methods can share one input format.
*   Maze sizes, rewards, and the action set.
