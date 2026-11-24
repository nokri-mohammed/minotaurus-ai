# minotaurus-ai

*   **Author:** nokri-mohammed
*   **Status:** Draft (Overview & Goals, Technical Plan, Alternatives approved 2026-11-21)
*   **Date:** 2026-11-20

--------------------------------------------------------------------------------

## MVP scope change (CEO, 2026-11-21)

The MVP is a **local, single-player arena**, not the online race:

*   One arena page on this machine (server and page on 127.0.0.1). The player loads their own
    `.onnx` brain, picks the level, and starts a run.
*   The brain runs on the local game server (rules still in one place); the page draws the dot.
*   Each run has a **timeout** (the step limit) and a **timer**: time taken (game time and steps), or
    "timed out".
*   Every attempt is saved in the browser (`localStorage`): date, brain name, method, level, result,
    steps, time. The page lists all previous attempts.
*   **Post-MVP:** the live online 1v1 race (rooms, two players, IP-gated internet access, security
    review) as described in the sections below. Those sections stay as the target design.

MVP stages replace the table under "Stages":

| Stage | Builds | The CEO can check |
|---|---|---|
| 1 | Schemas, first level, engine, tests | `uv run pytest` passes; `minotaurus play` moves a random dot in the terminal |
| 2 | Trainer, both methods, export, `check-brain` | train both example configs; `play` shows each brain solving the level |
| 3 | Local arena server: upload one brain, run it with timeout and timer, stream ticks | a run from a test client |
| 4 | Arena page: load brain, pick level, watch the run, result, attempt history in the browser | the CEO runs a brain and sees all past attempts |

## Overview

minotaurus-ai is a learning project for reinforcement learning (RL). A dot must find the exit of a
2D maze. Each player trains their own "brain" for the dot with a command-line training script on
their own machine, choosing the method (a Q-table or a neural network) and its settings in a JSON
file. Training produces one `.onnx` file. Two players then load their brain files into a browser
race online: each joins from their own device, both dots start on the same square of the same
maze, the first to reach the exit wins, and a result screen shows the winner and finish times.
Mazes are level files with a difficulty, so new levels are added without code changes.

The game rules live in one place, a Python engine with the standard Gymnasium interface
(`reset()` and `step(action)`). The trainer uses the engine directly; a small game server wraps the
same engine with a WebSocket for the race; the browser page only draws.

## The Problem

The CEO wants to understand RL the way it is practised: a real training process that runs as a
script, writes progress and a model file, and a separate program that loads that file and shows the
trained agent acting, and to race brains against other people online. Browser demos that train inside the page hide this split between training and
using a model.

A maze is small enough to train on a normal CPU in minutes to hours, yet it shows the core ideas:
reward, exploration against exploitation, value estimates, and the difference between memorising
one maze (Q-table) and learning patterns that work on new mazes (neural network).

The project must also be built so the same structure can later train agents for harder games, such
as the living-village world, without redesigning the trainer.

## Goals

*   A training command, `train.py --config <file>.json`, that trains a maze brain with either a
    Q-table or a Deep Q-Network (DQN), using only the settings in the JSON file, and writes one
    `.onnx` brain file.
*   A JSON Schema for the config, so a wrong setting stops training with a message that names the
    setting.
*   Training that runs on a CPU and records metrics (reward, steps, success rate) and checkpoints
    during the run.
*   **Online two-player race:** two players on their own devices open the game page, each enters an
    avatar name and loads their own `.onnx` brain. Both join the same race (for example with a room
    code). The game server puts two dots on the same start square of one maze and runs both brains
    tick by tick; both browsers show the same race live.
*   **Result screen at the end:** the winner, each player's finish time (in game time and in steps),
    or "did not finish" when the step limit runs out, and a draw when both arrive on the same tick.
    Plus trails, step counters, a speed control and replay.
*   **Reachable from the internet (CEO, 2026-11-21):** players join from anywhere, not only the home
    network. The game server is a public service that accepts uploaded brain files, so it needs
    upload limits (file size, model size, run time per step), safe loading of untrusted `.onnx`
    files, and a security review by `security-specialist` before it goes live (team rule for
    anything exposed beyond the LAN). Hosting is on the homelab server, done by `homelab-it` with
    the CEO's go.
*   **Gated first, public later (CEO, 2026-11-21):** the MVP is reachable only from an allowlist of
    IP addresses (the CEO's and one friend's), enforced in front of the server (for example a
    Cloudflare Access or firewall rule), not by the game itself. The allowlist values live outside
    the repo. Opening it to everyone is a later stage. The gated phase is still beyond the LAN, so a
    short security review comes before the gate opens, and a full one before going public.
*   **Levels with difficulty:** the MVP ships one maze, but mazes are level files with a difficulty
    (for example easy, medium, hard), so more levels are added as files with no code change, and
    players can pick a level before the race.
*   One copy of the game rules (the engine), used by both the trainer and the race server.
*   An engine interface (Gymnasium) that lets a new game be added as a new environment, including a
    game written in another language through a socket-based `RemoteEnv`, with no change to the
    trainer.
*   Built one stage at a time, each stage usable and checked by the CEO before the next starts.

## Non-Goals

*   Training inside the browser.
*   GPU training or large networks.
*   Accounts, logins, or a shared public all-time leaderboard.
*   More than two players in one race.
*   3D graphics.
*   Going live on the internet before the race works locally and has passed the security review.
*   Open public access in the MVP: only allowlisted IPs.
*   Methods other than Q-table and DQN in the first stages (PPO is a later idea).
*   Connecting the living-village game now: only keeping the interface ready for it.

## Open Questions

*   **Public or private repository**, and when the project folder is created.
*   **Maze sizes, reward values and the action set** (four moves, or also "stay").

## Technical Plan (Architecture)

### Components

```text
                    levels/*.json  (maze, difficulty, start, exit)
                           │
                ┌──────────▼───────────┐
                │ engine  (Python)     │  the only copy of the rules
                │ MazeEnv: Gymnasium   │  reset() · step(action)
                │ Race: 2 dots, 1 maze │  ticks, finish, draw, step limit
                │ observe(): numbers   │  the input every brain receives
                └───┬──────────────┬───┘
       imports      │              │      imports
     ┌──────────────▼───┐   ┌──────▼──────────────────────────┐
     │ trainer (CLI)    │   │ server (Python, FastAPI)        │
     │ train --config   │   │ rooms · brain upload · race     │
     │ qtable | dqn     │   │ runs both .onnx with onnxruntime│
     │ → brain.onnx     │   │ broadcasts each tick            │
     │ metrics, ckpts   │   └──────▲──────────────────────────┘
     └──────────────────┘          │ WebSocket (JSON) + HTTP upload
                            ┌──────┴──────────────────────────┐
                            │ web (TypeScript, Bun, Vite)     │
                            │ lobby · race canvas · results   │
                            │ draws only, decides nothing     │
                            └─────────────────────────────────┘
```

### Engine (Python package `minotaurus`)

*   **Levels** are JSON files in `levels/`, checked by `schemas/level.schema.json`: id, name,
    difficulty (`easy`, `medium`, `hard`), the grid as rows of characters (`#` wall, `.` floor,
    `S` start, `E` exit), and an optional step-limit factor (default 4 x the shortest path). The
    MVP ships one easy level. A new level is a new file.
*   **MazeEnv** implements the Gymnasium interface for one dot: actions are up, down, left, right;
    a move into a wall leaves the dot in place. Default rewards: +1 at the exit, -0.01 per step,
    -0.05 for bumping a wall. The episode ends at the exit or the step limit.
*   **Race** runs two dots on one level. Each tick both brains choose a move from the same state, and
    both moves apply at once. Dots do not block each other. First to the exit wins; both on the same
    tick is a draw; a dot still out at the step limit does not finish. Finish time = ticks x tick
    length.
*   **observe()** turns the game state into the brain's input. Its format is the contract between
    training and racing, versioned as `obs_version`. See "Brain input" below.
*   **RemoteEnv (later):** a class with the same `reset()` and `step()` that forwards them over a
    socket to a game written in another language. Not built in the MVP; the interface keeps it
    possible.

### Trainer (CLI)

*   `minotaurus train --config my-brain.json` (a `train.py` wrapper also works).
*   The config is checked against `schemas/brain-config.schema.json`: `name`, `method` (`qtable` or
    `dqn`), `levels` (level ids, or a difficulty for random levels), `episodes`, `seed`, and a block
    of settings for the chosen method (Q-table: learning rate, gamma, epsilon start, end and decay;
    DQN: hidden layers, learning rate, batch size, gamma, replay buffer size, target network update
    interval, epsilon schedule).
*   Output in `runs/<name>/<date-time>/`: `metrics.jsonl` (one line every N episodes: average reward,
    steps, success rate, epsilon, loss), `checkpoints/`, the config used, and `brain.onnx`.
*   **Export:** DQN with `torch.onnx.export`; Q-table as a small ONNX graph built with
    `onnx.helper`. Every `brain.onnx` carries metadata: avatar name, method, `obs_version`, and the
    ids of the levels it trained on.

### Server (Python, FastAPI)

*   **Rooms:** a player creates a room and gets a short code; the friend joins with it. Each sets a
    name and uploads a brain. The room creator picks the level and the speed and presses Start.
*   **Brain upload** (HTTP POST, untrusted input): max file size 1 MB; parsed with `onnx`; must have
    exactly one input of the expected shape and one output of 4 values; only an allowlist of ONNX
    operators; matching `obs_version`. Rejected files get a clear message.
*   **Running brains:** `onnxruntime` on the CPU, one thread per session, a time limit per step; a
    brain that errors or runs too long loses the race.
*   **Race loop:** one tick every 100 ms at normal speed. After each tick the server sends both
    players the dot positions and the tick number; at the end it sends the result (winner, each
    finish time and steps, or did not finish). The full move list is kept for replay.
*   **Network:** the server listens on 127.0.0.1 inside its container. Access from the internet goes
    through the homelab's Cloudflare tunnel with an IP allowlist (the CEO's and a friend's) in front.

### Web page (TypeScript, React with React Aria Components, Bun, Vite)

*   Screens: **lobby** (name, brain file, create or join a room, level picked by difficulty),
    **race** (canvas: maze, two coloured dots, fading trails, step counters, speed control), and
    **result** (winner, finish times, replay button).
*   A win count per avatar name is kept in the browser (`localStorage`).
*   It never runs game rules or brains; it only draws server messages.

### Messages (WebSocket, JSON)

*   Browser to server: `create_room`, `join_room {code, name}`, `choose_level {level_id}`,
    `set_speed {factor}`, `start`, `replay`.
*   Server to browser: `room {code, players, level, ready}`, `tick {n, dots: [{name, x, y}]}`,
    `result {winner, players: [{name, finished, ticks, seconds}]}`, `error {message}`.
*   Brain upload is a separate HTTP call: `POST /rooms/{code}/brain`.

### Brain input (CEO decision 2026-11-21: local view around the dot)

`observe()` gives every brain the same input each tick, whatever the maze size (`obs_version` 1):

*   A **5 x 5 window centred on the dot**, as three layers of 0s and 1s: walls (squares outside the
    maze count as walls), the exit (if it is inside the window), and **visited** (squares this dot
    has already stepped on in this race or episode).
*   The **direction to the exit**: two numbers, -1, 0 or 1 for left or right and for up or down.
*   Flattened into one vector of 77 numbers (3 x 25 + 2), shape `[1, 77]`. Output: 4 scores (up,
    down, left, right); the server takes the highest.

Why the visited layer: with a small window the brain cannot see the end of a long dead end, and
without memory it walks back into the same corridor. Marking where it has been lets it learn to
prefer new squares, without a recurrent network.

**Change (repo owner decision 2026-11-24, still `obs_version` 1):** the visited layer is a visit
count, min(visits, 3) as a raw number (0, 1, 2, 3); a bump counts as one more visit of the dot's own
square. A square walked on once is still 1, so a brain trained on the old yes/no layer sees the same
input until it revisits a square. Exported brains carry `visited="counts"`; the loader warns (does
not refuse) for brains without it. Research behind it: `docs/research/2026-11-23-official-brain.md`
(the wall trap) and TRAINING.md.

**Q-table with this input:** the table is keyed on the window and direction, not on the square, so
the same table can play on any maze (weaker than on its training maze). The ONNX export turns the
77 numbers into one whole number key (each 0/1 becomes a bit), maps the key to a table row with the
`LabelEncoder` operator (unknown keys go to a row of zeros), and returns that row. `LabelEncoder`
(domain `ai.onnx.ml`) is on the server's operator allowlist.

**Known limit:** a 5 x 5 view plus exit direction can still be fooled by mazes where the exit
direction points into a wall for a long way (big hard levels).

**Ready for a wider view and a memory network after the MVP (CEO, 2026-11-21).** The MVP builds
only a 5 x 5 window and no memory, but the contract leaves room for both, so adding them later
changes no message, file format or race rule:

*   Every `brain.onnx` declares its needs in its metadata: `window` (MVP: 5) and `memory` (MVP:
    none; later the size of its memory state).
*   `observe()` takes the window size as a parameter, and the server builds each brain's input at
    the size that brain declares. Input length = 3 x window x window + 2.
*   For a memory brain, the ONNX model gets one extra input and one extra output (its memory state).
    The server keeps each brain's state between ticks, starts it at zeros, and feeds it back every
    tick. The race loop is written with this slot from the start (empty in the MVP).
*   The trainer's config schema reserves `observation.window` and `dqn.memory` (rejected with "not
    supported yet" in the MVP).

### Deployment (later stages)

*   One Docker image for the server and the built web page, with a memory cap, no outbound network,
    run on the homelab server by `homelab-it` with the CEO's go.
*   Training on the server uses the same image with the trainer command.

## Alternatives Considered

### Alternative A: Train in the browser (TypeScript)

*   **Pros**: Nothing to install; training is visible live in the page.
*   **Cons**: Hides the real split between a training process and a program that uses the model;
    limited by the browser tab.
*   **Reason for Rejection**: Rejected by author: the goal is to see a real training process run as
    a script on a machine or server, producing a model file.

### Alternative B: Rust with burn for training

*   **Pros**: Lower memory use (tens of MB instead of hundreds); one binary.
*   **Cons**: Younger library, far fewer RL examples, more work for ONNX export; a different stack
    from later LoRA fine-tuning.
*   **Reason for Rejection**: Rejected by author: Python (PyTorch, Gymnasium) is the standard for
    learning RL; the memory saving does not matter at this size.

### Alternative C: Go or Bun for training

*   **Pros**: Light and fast to start.
*   **Cons**: Weak neural-network libraries.
*   **Reason for Rejection**: Rejected by author: not suited to DQN training.

### Alternative D: Two copies of the rules (Python for training, TypeScript in the page)

*   **Pros**: The race page could be a static site with no server.
*   **Cons**: The same rules in two languages; a change to one copy silently breaks brains in the
    race. Impossible to keep in step for complex games.
*   **Reason for Rejection**: Rejected by author: rules must live in one place so the design scales to
    complex games such as the living-village world.

### Alternative E: Trainer talks to the game server over the socket

*   **Pros**: The trainer works with any game server in any language.
*   **Cons**: Every step crosses a socket: 10 to 100 times slower training.
*   **Reason for Rejection**: Rejected by author: the trainer imports the Python engine directly; a
    `RemoteEnv` over a socket stays available for future games in other languages.

### Alternative F: A full game engine with an RL toolkit (Godot RL Agents, Unity ML-Agents)

*   **Pros**: Physics, 3D and an editor; proven on complex games.
*   **Cons**: Heavy; hides the internals.
*   **Reason for Rejection**: Rejected by author: the CEO wants to learn and control every part, and
    run it lightly on a mini server.

### Alternative G: YAML config

*   **Pros**: Comments allowed; easier to hand-edit.
*   **Cons**: Needs a parser library; the page cannot write it as easily.
*   **Reason for Rejection**: Rejected by author: JSON with a JSON Schema.

### Alternative H: Neural network only, no Q-table

*   **Pros**: One method, less code.
*   **Cons**: No way to compare methods.
*   **Reason for Rejection**: Rejected by author: the trainer offers both, chosen per config.

### Alternative I: Brain input as a full grid picture, or a different input per method

*   **Pros**: Full grid: the brain sees the whole maze. Per method: each method gets its natural input.
*   **Cons**: Full grid breaks when mazes grow past a fixed size; per method means two formats to
    keep in step for every future game.
*   **Reason for Rejection**: Rejected by author: a 5 x 5 local view with a visited layer and exit
    direction, the same size for any maze.

### Alternative J: Home network only, or fully public from the start

*   **Pros**: Home only: no exposure. Public: anyone can play.
*   **Cons**: Home only: the friend cannot join. Public: untrusted uploads from anyone before the
    server is proven.
*   **Reason for Rejection**: Rejected by author: internet access gated to two IP addresses first,
    public later after a security review.

--------------------------------------------------------------------------------

## Non-Functional Requirements

*   **Security & Privacy:** uploaded `.onnx` files are untrusted: size limit 1 MB, operator
    allowlist, fixed input and output shapes, one CPU thread and 50 ms per step, run inside a
    container with a memory cap and no outbound network. Access gated to two IP addresses in front of
    the server; the addresses live outside the repo. Rooms expire after 30 minutes idle; at most 10
    rooms at once. A short `security-specialist` review before the gate opens, a full one before
    public access.
*   **Performance:** training on a CPU; the MVP maze trains in minutes. The server holds tiny models
    (under 1 MB) and runs one step per brain every 100 ms.
*   **Rollout:** local first (both browsers on this machine), then gated on the homelab, then public.

### Future Improvements

*   Wider view and memory network (contract already reserves `window` and `memory`).
*   Training dashboard: reward and success curves from `metrics.jsonl`, checkpoint replays.
*   More levels per difficulty; random level generation for training.
*   Long training runs on the homelab server in the same Docker image.
*   Public access after a full security review; a shared leaderboard.
*   `RemoteEnv` for games in other languages (for example living-village).
*   A second method (PPO).

--------------------------------------------------------------------------------

## Detailed Implementation Plan

The project lives in `projects/minotaurus-ai/` (team layout: Claude files in `.claude/`). One solo
lead, `minotaurus-ai-dev` (sonnet). Python 3.12 managed with `uv`; web with Bun.

### Target Files to Create

#### Project and team

1.  `.claude/CLAUDE.md` (Create): project rules: one copy of the rules in `minotaurus/`, brain input
    contract `obs_version` 1, untrusted uploads, gated access, one stage at a time on the CEO's word.
2.  `.claude/agents/minotaurus-ai-dev.md` (Create): the solo lead's brief and rights.
3.  `.claude/settings.json` (Create): allow `uv`, `bun`, `pytest`, local git; ask for push and `gh`.
4.  `.claude/docs/TEAM.md`, `.claude/docs/LESSONS.md`, `.claude/docs/tickets/` (Create): team
    diagram and log, lessons, one ticket per stage.
5.  `.claude/docs/plans/minotaurus-ai.md` (Create): this design, final copy.
6.  `README.md`, `LICENSE` (Create): what it is, how to train, how to race; licence per the open
    question.
7.  `.gitignore` (Create): `runs/`, `.venv/`, `node_modules/`, `web/dist/`.

#### Contracts

8.  `schemas/level.schema.json` (Create): level file format (id, name, difficulty, grid rows, optional
    step-limit factor). Grid must have one `S` and one `E`, be rectangular, and be solvable (checked
    in code).
9.  `schemas/brain-config.schema.json` (Create): training config (name, method, levels, episodes,
    seed, `qtable` or `dqn` block; reserved `observation.window` and `dqn.memory`).
10. `schemas/messages.schema.json` (Create): every WebSocket message in both directions. Server and
    web tests validate sample messages against it, so the two sides cannot drift.
11. `levels/easy-01.json` (Create): the MVP level, about 9 x 9.
12. `examples/qtable-brain.json`, `examples/dqn-brain.json` (Create): ready-to-run configs.

#### Engine (`minotaurus/`)

13. `minotaurus/levels.py` (Create): load and validate a level; shortest path by breadth-first search
    for the step limit and the solvable check.
14. `minotaurus/observe.py` (Create): `observe(state, dot, window=5) -> 77 floats` (walls, exit,
    visited, exit direction); `obs_version = 1`.
15. `minotaurus/env.py` (Create): `MazeEnv(gymnasium.Env)`: `Discrete(4)` actions, `Box` observation
    from `observe()`, rewards +1 exit, -0.01 step, -0.05 wall bump, end at exit or step limit.
16. `minotaurus/race.py` (Create): two dots, one level; `tick(actions)` applies both moves at once;
    result with winner, draw, finish ticks and seconds, did not finish; full move log for replay.
    Takes brains as plain functions (observation in, action out), so it does not depend on ONNX.

#### Trainer

17. `minotaurus/brains/qtable.py` (Create): tabular Q-learning keyed on the observation; epsilon
    schedule; returns the table.
18. `minotaurus/brains/dqn.py` (Create): network (hidden layers from config), replay buffer, target
    network, epsilon schedule, Adam, Huber loss.
19. `minotaurus/train.py` (Create): reads and validates the config, picks the method, runs episodes,
    writes `runs/<name>/<date-time>/` (`metrics.jsonl`, `checkpoints/`, config copy, `brain.onnx`).
20. `minotaurus/export.py` (Create): DQN via `torch.onnx.export`; Q-table as an ONNX graph (bits to
    key, `LabelEncoder` to row, `Gather`); metadata: name, method, `obs_version`, `window`,
    `memory`, trained levels.
21. `minotaurus/onnx_brain.py` (Create): load an `.onnx` safely (size limit, `onnx.checker`, operator
    allowlist, shape and metadata checks), wrap it as a brain function with a per-step time limit.
    Used by the server and by the CLI.
22. `minotaurus/cli/` (Create, one file per command): `minotaurus train --config`, `minotaurus check-brain <file>`,
    `minotaurus play <brain> --level <id>` (watch one brain in the terminal), `minotaurus serve`.

#### Server (`minotaurus/server/`)

23. `minotaurus/server/rooms.py` (Create): room codes, two player slots, level choice, speed, state
    (waiting, ready, racing, finished), expiry after 30 minutes idle, max 10 rooms.
24. `minotaurus/server/app.py` (Create): FastAPI: `POST /rooms/{code}/brain` (upload through
    `onnx_brain`), `GET /levels` (ids, names, difficulty), WebSocket `/ws` for the messages, the race
    loop (100 ms per tick times speed), serves the built web page. Binds 127.0.0.1.

#### Web (`web/`)

25. `web/package.json`, `web/tsconfig.json`, `web/vite.config.ts` (Create): Bun, TypeScript, Vite;
    dev proxy for `/ws`, `/rooms`, `/levels` to the server.
26. `web/index.html`, `web/src/main.ts` (Create): screen switching (lobby, race, result).
27. `web/src/protocol.ts`, `web/src/net.ts` (Create): message types and the WebSocket client.
28. `web/src/lobby.ts` (Create): name, brain file upload, create or join room, level picker by
    difficulty, speed, Start.
29. `web/src/race.ts` (Create): canvas drawing: maze, two dots in player colours, fading trails, step
    counters.
30. `web/src/result.ts`, `web/src/scoreboard.ts` (Create): winner, finish times and steps, replay;
    wins per name in `localStorage` (wrapped in try/catch).

#### Deployment (stage 7, later)

31. `docker/Dockerfile` (Create): Python and the built web page in one image; non-root user.
32. Homelab stack and the Cloudflare tunnel with the IP allowlist: done by `homelab-it` in its own
    ticket, values outside this repo.

#### Tests

33. `tests/test_levels.py`, `tests/test_observe.py`, `tests/test_env.py`, `tests/test_race.py`
    (Create): rules, edge cases (window at the maze edge, bump into wall, both finish on one tick,
    step limit).
34. `tests/test_export.py` (Create): for both methods, the ONNX output equals the in-memory brain's
    output on the same observations.
35. `tests/test_onnx_brain.py` (Create): rejects oversize files, wrong shapes, forbidden operators,
    wrong `obs_version`, slow brains.
36. `tests/test_server.py` (Create): two clients create and join a room, upload brains, race,
    receive ticks and one result; messages match `messages.schema.json`.
37. `web/src/*.test.ts` (Create): message samples match the schema; scoreboard counts.

### Stages (one ticket each, next one only on the CEO's word)

| Stage | Builds | The CEO can check |
|---|---|---|
| 1 | Project files, schemas, level, engine, tests | `uv run pytest` passes; `minotaurus play` with a random brain moves a dot in the terminal |
| 2 | Trainer, both methods, export, `check-brain` | train both example configs; `play` shows each brain solving the level |
| 3 | Server: rooms, upload, race loop | a race between two brains from a test client |
| 4 | Web page: lobby, race, result | two browser tabs on this machine race two brains |
| 5 | Polish: replay, speed, scoreboard, difficulty picker | full MVP locally |
| 6 | Docker, homelab, tunnel with IP allowlist (homelab-it), short security review | the CEO and the friend race online |

### Verification Plan

*   **Build:** `uv sync`; `cd web && bun install && bun run build`.
*   **Unit tests:** `uv run pytest`; `cd web && bun test`.
*   **Static analysis:** `uv run ruff check`; `bun run typecheck`.
*   **End to end:** train `examples/qtable-brain.json` and `examples/dqn-brain.json`, start
    `minotaurus serve`, open two browser tabs, race the two brains on `easy-01`, see a result screen.
