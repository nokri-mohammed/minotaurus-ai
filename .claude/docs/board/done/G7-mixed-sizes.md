# G7: mixed maze sizes and the fixed levels as a score

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** engine, trainer, cli
- **Model:** opus
- **Rule from the CEO:** extend Mo's work, do not refactor it.

## Why

The shaped DQN scores 84% on made 9x9 mazes (exit inside) but finishes 1 of 6 fixed levels
(sizes 9 to 21, exit in the outer wall). It never saw other sizes or border exits.

## How to build it (tests first)

1. `generated.sizes` (optional list): each pool is split evenly over these sizes and interleaved.
2. `evaluate.score_fixed_levels`: the six hand-made levels as an extra score (not used to choose).
3. `train` writes `fixed_levels.json`; the command prints it; the seed table shows it.
4. Example config `data/examples/dqn-mixed-brain.json`.

## Report

- **Done (extension only):** `generated.sizes`, `_draw_mixed` and `build_pools(sizes=...)`,
  `score_fixed_levels`, `fixed_levels.json`, a line in the train summary and a column in the seed
  table, `data/examples/dqn-mixed-brain.json`, TRAINING.md section.
- **Tests:** `uv run pytest` 322 passed, ruff clean.
- **Left:** the result of training the mixed config is in the next message to the CEO (it takes
  longer than size 9 alone).
- **Lessons:** in LESSONS.md.
