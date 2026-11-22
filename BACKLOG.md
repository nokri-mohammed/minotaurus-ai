# Backlog

Everything that needs doing and is not started, with how to do it. The CEO pulls items into Todo
on the boards: [Python](minotaurus/BOARD.md), [Web](web/BOARD.md). On a pull, the item moves to a
card file in `.claude/docs/board/todo/` (cut, not copied). Design: `.claude/docs/plans/minotaurus-ai.md`.

Order: S2 (in progress, see board) -> S3. S4 (the page) is already built against the message contract and a mock; S3 must implement that contract.

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
