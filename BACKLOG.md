# Backlog

Everything that needs doing and is not started, with how to do it. The CEO pulls items into Todo
on the boards: [Python](minotaurus/BOARD.md), [Web](web/BOARD.md). On a pull, the item moves to a
card file in `.claude/docs/board/todo/` (cut, not copied). Design: `.claude/docs/plans/minotaurus-ai.md`.

The MVP (S1 to S4) is done, and so are G1, G2, G4 and the later cards G6 to G32 and T1 (see the boards). The fake arena (`web/mock/`, `dev --mock`) is deleted. Open: G3, G5, G33, then P1 and P2 after the MVP.

---

## Python

### G3: random and shortest-path players

**Goal.** A floor and a ceiling to judge any brain, and built-in arena opponents. They run at
runtime (scoring and the arena), never in training.

1. **Random player:** a seeded function `obs -> move` (same seed, same moves, replayable).
2. **Shortest-path player:** built from the level, not from the 77 numbers (the window cannot see
   the maze), so it is a Python player and not an `.onnx` file.
3. **Arena:** the opponent slot takes "Random player" or "Shortest path" without an upload. Needs S3.

### G5: decision log on the real test

**Goal.** On the real test only (never in training), write what the brain saw and chose at each
step, so a run can be replayed and debugged. Needs G1 and S3.

1. **Per step:** position, the 77 inputs (or a readable view), the 4 scores, the chosen move. (G12 already saves position, move and game time per step in the page; this adds what the brain saw and its scores.)
2. **Where:** a file next to the result; off by default, switched on for test runs.

### G33: upload and export a maze

**Goal.** Share a maze as a file: export any maze (hand-made, test or random) and load a maze
someone else made, then run a brain on it in the arena. Nothing from an upload is trusted.

1. **Format:** the existing level JSON (`data/schemas/level.schema.json`), one maze per file. Export
   adds nothing new; check that a random maze (`gen-...` id) exports the same shape.
2. **Export:** `GET /levels/{id}/export` returns the level file; the page gets an "Export maze"
   button next to the level dropdown (Arena and Random maze page).
3. **Upload:** `POST /levels` takes a level JSON. Pydantic checks it against the schema, then the
   engine checks the rules: size limit (file bytes, rows, columns), one start, one exit, only known
   cell characters, an exit that can be reached from the start. A bad file is refused with the
   reason. An uploaded maze gets an id from the sha256 of its content, so the same file is the same
   maze.
4. **Keep:** uploaded mazes live in the arena database (`var/arena.db`), not in `data/levels/`.
   They show in the dropdown in an "Uploaded" group. They are left out of "Run all levels" and of
   the star rating (like test mazes, the CEO decides).
5. **Page:** an "Upload maze" file button (`.json`) through `web/src/services/`; zod schema for the
   reply in `web/src/protocol.ts`; update `data/schemas/messages.schema.json` and
   `message-samples.json`.
6. **CLI (optional):** `minotaurus levels export <id>` and `minotaurus levels import <file>`.
7. **Tests first:** valid file, too big, no exit, unreachable exit, wrong characters, same file twice
   gives one maze, export then upload round trip.

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
