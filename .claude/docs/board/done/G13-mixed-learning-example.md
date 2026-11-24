# G13: mixed-size example with the R3 recipe

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** trainer (example config, docs)
- **Model:** opus
- **CEO go:** 2026-11-24 ("write it I will run it")

## Goal

A config for sizes 9, 11 and 13 that uses Mo's R3 recipe, so the mixed-size question gets a fair run.

## Report

- **Done:** `data/examples/dqn-mixed-learning-brain.json`: the same mazes as `dqn-mixed-brain.json`
  (maze_seed 1, 600 / 120 / 120, border exit), 128-128 network, 15000 tries, `epsilon_decay` 0.997,
  replay 50000, wall mask, novelty bonus 0.02, revisit penalty 0.01, `eval_every` 250, `patience` 8,
  `seeds` [1, 2, 3, 4] and `parallel` 4. TRAINING.md says what the first mixed run did and why.
- **Tests:** a test checks the recipe and that the pool settings equal the first mixed example's.
  Not trained by me: the CEO runs it (`uv run minotaurus train --config data/examples/dqn-mixed-learning-brain.json`).
- **Left:** the run itself (about 1 to 1.5 hours on 4 cores).
- **Lessons:** an example config is a recipe too: copy the best known settings, not the first ones.
