# Backlog

Everything that needs doing and is not started, with how to do it. The CEO pulls items into Todo
on the boards: [Python](minotaurus/BOARD.md), [Web](web/BOARD.md). On a pull, the item moves to a
card file in `.claude/docs/board/todo/` (cut, not copied). Design: `.claude/docs/plans/minotaurus-ai.md`.

Order: S3 next (S1, S2, S4 are done). S4 (the page) is built against the message contract and a fake arena inside Vite (`web/mock/`); S3 must implement that contract, then `web/mock/` and the `dev:mock` script are deleted.

---

## Python

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

### G1: maze generator with train, validation and test sets

**Goal.** Many seeded mazes instead of one hand-made level, so a brain is tested on mazes it never
saw. Comes from the proposal doc (Mo, 2026-11-21); the branch `feat/procedural-levels` is not in
this repo yet, so start by reviewing it.

**How to build it (tests first):**

1. **Review the branch:** the 77+ tests still pass, `obs_version` 1 is unchanged, levels stay valid
   against `level.schema.json`, brains stay under the 1 MB limit.
2. **Pools:** seeded generator; train pool, validation pool, test mazes on demand; compare maze
   layouts, not only seeds, so no test maze appears in training.
3. **Metadata:** save pool sizes and seeds in the config and in the `.onnx` metadata; refuse to
   score when they do not match.

### G2: better metrics (small)

**Goal.** See wandering and compare brain sizes fairly.

1. **Path ratio:** steps divided by the shortest path, in `metrics.jsonl` and in the arena
   `result` message (`shortest_path_length` already exists).
2. **Parameter count:** in the metrics and in the `.onnx` metadata.

### G3: random and shortest-path players

**Goal.** A floor and a ceiling to judge any brain, and built-in arena opponents. They run at
runtime (scoring and the arena), never in training.

1. **Random player:** a seeded function `obs -> move` (same seed, same moves, replayable).
2. **Shortest-path player:** built from the level, not from the 77 numbers (the window cannot see
   the maze), so it is a Python player and not an `.onnx` file.
3. **Arena:** the opponent slot takes "Random player" or "Shortest path" without an upload. Needs S3.

### G4: best brain on validation

**Goal.** Export the best checkpoint on the validation mazes, not the last one (the last can be
worse). Needs G1.

1. Score on validation every N episodes; keep the best; export it.
2. Log which episode was exported.

### G5: decision log on the real test

**Goal.** On the real test only (never in training), write what the brain saw and chose at each
step, so a run can be replayed and debugged. Needs G1 and S3.

1. **Per step:** position, the 77 inputs (or a readable view), the 4 scores, the chosen move.
2. **Where:** a file next to the result; off by default, switched on for test runs.

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

### P1 (after MVP): race page for two players

Lobby (name, brain, create or join a room, level picker by difficulty), race canvas with two
coloured dots, speed control, result screen, replay, wins per name in `localStorage`.
