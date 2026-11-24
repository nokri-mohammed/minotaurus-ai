# G8: saved test mazes in the portal, the "impossible" difficulty, a bigger mixed-size example

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** engine, trainer, server, web
- **Model:** opus
- **Rule from the CEO:** extend Mo's work, do not refactor it. Difficulty stays tied to size (option 1).

## Goal

1. `data/levels/test-mazes/`: 12 files (4 per size, sizes 9, 11, 13) copied from the real test pile
   of the example config, so you can watch them in the portal. They never enter training.
2. A fourth difficulty `impossible` and one hand-made level `impossible-01` (41 x 41).
3. `data/examples/dqn-mixed-brain.json` becomes sizes [9, 11, 13], 600 / 120 / 120 mazes. (Size 9 has
   only 322 different mazes, so 700 / 150 / 150 would not fit: 333 per size.)

## How to build it (tests first)

- `load_test_mazes`, `load_portal_levels` (hand-made + test mazes) in `levels.py`; the hand-made
  list stays as it is, so `{"difficulty": "easy"}` in a config can never pick a test maze.
- `trainer/test_mazes.py` writes the files from the example config; a test checks they match the
  test pile and are in no other pile.
- `impossible` in the level schema, messages (Pydantic, zod, JSON schema), the order table.

## Report

- **Done:** `impossible` difficulty (level schema, messages in Pydantic, zod and JSON schema, order
  table, a valid sample); `data/levels/impossible-01.json` (41 x 41, shortest path 561, the best of
  300 seeds); `load_test_mazes` and `load_portal_levels`; the server lists and runs the test mazes;
  `trainer/test_mazes.py` and 12 saved files; `dqn-mixed-brain.json` is now sizes 9, 11, 13 with
  600 / 120 / 120.
- **Tests:** `uv run pytest` 330 passed, ruff clean; `bun test` 37 passed, typecheck and build clean.
- **Left:** the mixed example is not trained yet (the CEO said not to start training). The page lists
  the test mazes in the same dropdown as the others (no separate group yet). The generator never
  makes `impossible`; only the hand-made level has it.
- **Changed from the plan:** 600 / 120 / 120 instead of 700 / 150 / 150, because size 9 has only 322 mazes.
- **Lessons:** in LESSONS.md.
