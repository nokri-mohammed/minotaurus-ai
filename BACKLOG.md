# Backlog

Everything that needs doing and is not started, with how to do it. The CEO pulls items into Todo
on the boards: [Python](minotaurus/BOARD.md), [Web](web/BOARD.md). On a pull, the item moves to a
card file in `.claude/docs/board/todo/` (cut, not copied). Design: `.claude/docs/plans/minotaurus-ai.md`.

Order: S2 -> S3 -> S4 (S4 needs S3's messages; S3 needs S2's brain loader).

---

## Python

### S2: trainer, both methods, ONNX export, `check-brain`

**Goal.** `minotaurus train --config <file>.json` trains a brain with a Q-table or a DQN and writes
`brain.onnx`. `check-brain` validates a file. `play --brain <file>` shows a brain solving `easy-01`.

**How to build it (tests first for each step):**

1. **Config check** (`minotaurus/trainer/config.py`): load JSON, validate against
   `data/schemas/brain-config.schema.json` (already written), and turn the first error into a
   message naming the setting. Resolve `levels` ids with `load_level_by_id`.
2. **Examples** (`data/examples/qtable-brain.json`, `dqn-brain.json`): small, ready to run on
   `easy-01`. Tests validate both against the schema.
3. **Q-table** (`trainer/qtable.py`): table is a dict keyed on the whole observation (the 77 numbers
   turned into one integer: exit direction as 2 x 2 bits plus the 75 window bits). Update rule
   `Q[s,a] += lr * (r + gamma * max Q[s'] - Q[s,a])`, epsilon-greedy with the decay from config,
   unseen keys start at zeros. Test: on a 1 x N corridor it learns to go right in a few episodes.
4. **DQN** (`trainer/dqn.py`, needs `torch`, CPU build): MLP 77 -> hidden layers from config -> 4,
   replay buffer, target network copied every `target_update` steps, Adam, Huber loss, epsilon
   schedule. Test: loss drops on a fixed batch; one training step changes the weights.
5. **Training loop** (`trainer/train.py`): per episode run `MazeEnv`, call the method, every N
   episodes append one line to `runs/<name>/<date-time>/metrics.jsonl` (average reward, steps,
   success rate, epsilon, loss), write `checkpoints/`, copy the config, export at the end. Seeded:
   same seed gives the same metrics (test).
6. **Export** (`trainer/export.py`): DQN with `torch.onnx.export`; Q-table built with
   `onnx.helper`: 77 floats -> multiply by powers of two and sum to one integer key ->
   `LabelEncoder` (domain `ai.onnx.ml`) maps key to row index (unknown key -> a row of zeros) ->
   `Gather` the Q-row. Both carry metadata: name, method, `obs_version`, `window`, `memory`, level
   ids. **Test: the ONNX output equals the in-memory brain on the same observations.**
7. **Brain loader** (`minotaurus/brain/onnx_brain.py`): safe load with size limit (1 MB),
   `onnx.checker`, operator allowlist, input `[1,77]` and output 4 checks, `obs_version` check,
   per-step time limit with `onnxruntime`; returns a plain function `obs -> action`. Tests reject
   a big file, wrong shape, forbidden operator, wrong version, slow model. S3 reuses it.
8. **CLI:** `check-brain <file>` prints OK or the reason; `play --brain <file> --level <id>`.

**New dependencies (CEO go needed):** `torch` (CPU), `onnx`, `onnxruntime`.

**You can check:** train both examples; `play --brain` shows each solving `easy-01`.

**Risks.** Q-table size explodes on big mazes (fine for `easy-01`). DQN may need tuning of
epsilon decay to solve in minutes on CPU.

### S3: local arena server

**Goal.** A server on 127.0.0.1: upload one brain, run it on a chosen level with a timeout and a
timer, stream ticks, send the result. Depends on S2 (`onnx_brain`).

**How to build it (tests first):**

1. **Messages** (`data/schemas/messages.schema.json`): `run_started`, `tick {n, x, y}`,
   `result {status: finished|timed_out|error, steps, seconds}`, `error {message}`. Tests validate
   samples, and the web tests will reuse the same file.
2. **Run loop** (`server/arena.py`): `MazeEnv` plus the loaded brain; one tick per 100 ms at normal
   speed; timeout is the level step limit; game time = ticks x 0.1 s; a brain that errors or runs
   over 50 ms in a step ends the run with `error`.
3. **HTTP/WebSocket** (`server/app.py`): `GET /api/levels` (id, name, difficulty), `POST
   /api/brain` (multipart, goes through `onnx_brain`, returns brain name and method),
   `WS /ws/run {level_id}` streams the messages. One brain and one run at a time. Binds 127.0.0.1.
4. **Test client** (`tests/test_server.py`): upload a trained example, run, read ticks and one
   result; a bad upload is refused with a clear message.

**You can check:** a run from the test client, and from `curl` plus a WebSocket client.

### P1 (after MVP): live online 1v1

Rooms with short codes, two players with their own brains on one maze, `Race` (already in the
engine) driven by the server, result with winner, draw, finish times, replay. Messages in the
design: `create_room`, `join_room`, `choose_level`, `start`, `replay`. Limits: 10 rooms, 30 minutes
idle expiry. Start only after the MVP is done.

### P2 (after MVP): online, gated to two IPs

Docker image (non-root, memory cap, no outbound network), homelab stack and Cloudflare tunnel with
an IP allowlist (values outside the repo), done by `homelab-it`; a short `security-specialist`
review before the gate opens. Start only after P1 works locally.

---

## Web

### S4: arena page

**Goal.** One page on 127.0.0.1: load a brain, pick a level, watch the run, see the result, and
see every past attempt. The page decides nothing; it draws server messages. Depends on S3.

**How to build it (tests first where there is logic, `bun test`):**

1. **Protocol** (`web/src/protocol.ts`, `net.ts`): types for the S3 messages; a test validates
   samples against `data/schemas/messages.schema.json` so the two sides cannot drift.
2. **Page** (`web/src/main.ts`, `arena.ts`): file picker uploads to `POST /api/brain`; level
   dropdown from `GET /api/levels`; Start opens `WS /ws/run`.
3. **Drawing** (`web/src/draw.ts`): canvas, maze from the level, the dot, a fading trail, step
   counter and timer.
4. **Result and history** (`web/src/history.ts`): result line (finished with steps and time, or
   timed out). Every attempt saved in `localStorage` (date, brain name, method, level, result,
   steps, time) inside try/catch, listed newest first. Test: add, list, survive broken storage.
5. `bun run typecheck` and `bun run build` stay clean.

**You can check:** run a brain, then reload the page and still see all past attempts.

### P1 (after MVP): race page for two players

Lobby (name, brain, create or join a room, level picker by difficulty), race canvas with two
coloured dots, speed control, result screen, replay, wins per name in `localStorage`.
