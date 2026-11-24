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

- **Result:** six commits, all options off by default except the visit-count input. Tests first
  for each; the suite grew from 224 tests on main to 296, passed three times in a row, and ruff
  is clean.
- **Old brains with the new input** (greedy, no random moves): official-dqn-shaped-v1 test size 9
  84% -> 86%, size 11 57% -> 67%, hand-made 1 -> 2 of 6 (medium-02 now finished); the size 11
  candidate from the 2026-11-24 runs 92% -> 92%, 65% -> 72%, hand-made 4 of 6 both times (it now
  fails hard-01 by pushing into a wall instead of by a loop). A bump now changes the input, which
  breaks some wall pushes even for a brain that never saw counts.
- **Smoke run** of `data/examples/dqn-learning-brain.json` cut to 500 tries: 2 min 23 s on one CPU
  core, training success up to 80%, check 37% and test 39% at size 11 with border exits; the
  brain carries `visited="counts"`, `wall_mask="true"` and every option in `training`.
- **Not done:** a full training run of the example config and its research numbers; the arena page
  does not show the visit counts.
- **Lessons:** see LESSONS.md (2026-11-24, L1).
