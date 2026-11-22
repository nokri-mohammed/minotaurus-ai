# Backlog

Everything that needs doing and is not started, with how to do it. The CEO pulls items into Todo
on the boards: [Python](minotaurus/BOARD.md), [Web](web/BOARD.md). On a pull, the item moves to a
card file in `.claude/docs/board/todo/` (cut, not copied). Design: `.claude/docs/plans/minotaurus-ai.md`.

Order: S1, S2, S3 (in progress) and S4 are the MVP. S3 implements the message contract the page was built against; when it lands, `web/mock/` and the `dev:mock` script are deleted. Next after S3: G1 to G5.

---

## Python

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
