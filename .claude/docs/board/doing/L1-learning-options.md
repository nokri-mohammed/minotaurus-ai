# L1: learning options (visit counts, wall mask, novelty and revisit rewards, generator, early stop)

- **Owner:** Mo (rackiavic), with Claude Code
- **Area:** engine, trainer, brain, server
- **Backlog:** not a backlog item; the TRAINING.md changes approved by the repo owner on
  2026-11-24, with one decision: no `obs_version` 2, the visit count is a breaking change inside
  `obs_version` 1.

## Goal

Give training the options the 2026-11-23 and 2026-11-24 research found useful, so a DQN can get
out of the wall trap (pushing into a wall forever) and the back-and-forth loop on the hand-made
levels. Every option is off by default, except the visit-count input, which replaces the yes/no
visited layer for everyone.

## Scope (do / do not)

Do, in this order, tests first:

1. Visited layer becomes a visit count in obs v1 (min(visits, 3), raw), `visited="counts"`
   metadata, loader warning for older brains, Q-table key stays yes/no, before/after numbers for
   the official and candidate brains.
2. `wall_mask` (training and play): never a move into a visible wall; config key and `.onnx`
   metadata, applied per brain by the arena.
3. `novelty_bonus` and `revisit_penalty` (training only, `dqn` block, default 0).
4. `border_exit` and `random_start` in the generated levels block (default false).
5. Early stop: `patience` (checks without improvement, default off).
6. TRAINING.md section, example config `data/examples/dqn-learning-brain.json`.

Do not: add `obs_version` 2, change the operator allowlist, change the rewards of the game.

## Done when

All six are in, full suite passes three times in a row, ruff is clean, the example config trains
(smoke run of about 500 tries), and the PR reports the before/after numbers.

## Report
