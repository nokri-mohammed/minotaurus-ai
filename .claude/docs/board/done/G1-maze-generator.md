# G1: maze generator with train, validation and test mazes

- **Owner:** minotaurus-ai-dev (the lead, no sub-agent)
- **Area:** engine, trainer
- **Model:** opus (done by the lead)
- **Backlog:** G1 in `BACKLOG.md`. Mo's branch never arrived; the CEO said to build it ourselves (2026-11-23).

## Goal

Many seeded mazes instead of one hand-made level, so a brain is scored on mazes it never trained on.

## How to build it (tests first)

1. `minotaurus/engine/generate.py`: `generate_maze(seed, size)` makes a valid Level, same seed same maze.
2. `minotaurus/engine/pools.py`: `build_pools(...)` gives train, validation and test mazes; no maze
   layout appears in two pools.
3. Config shape `"levels": {"generated": {...}}` (size, maze_seed, train, validation, test).
4. Training with generated mazes writes the pool settings into the `.onnx` metadata and a
   `scores.json` (train, validation, test success). Scoring refuses a brain whose pools differ.
5. `minotaurus train` prints the three scores.

## Scope

Do not touch `obs_version`, the 1 MB limit or the arena. G2 to G5 stay in the backlog.

## Report

- **Done:** `generate_maze`, `build_pools`, the `generated` config shape, `pool_settings`/`resolve_pools`,
  pool metadata in the `.onnx`, `trainer/evaluate.py` (`score_brain`, refuses other pools),
  `scores.json`, `train` prints the three scores, example `data/examples/qtable-generated.json`,
  TRAINING.md section.
- **Tests:** `uv run pytest`: 131 passed; ruff clean. Real run (size 9, 50/20/20 mazes, 6000
  episodes): train 92%, validation 0%, test 0%.
- **Left:** nothing in the card. The 0% is the real finding: the Q-table memorises. Ideas for a
  follow-up: more and bigger train pools, a DQN try, or a view that ignores the visited layer.
  Mo's branch was never reviewed (never arrived).
- **Lessons:** see LESSONS.md.
