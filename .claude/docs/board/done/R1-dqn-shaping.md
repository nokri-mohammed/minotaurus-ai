# R1: DQN on generated mazes (research and the options it needed)

- **Owner:** Mo (rackiavic), with Claude Code
- **Area:** trainer, brain, server
- **Backlog:** not a backlog item; three research rounds on 2026-11-23, approved by the repo owner.
  G4 has its own card.

## Goal

Find out why DQN scores 0% on generated mazes, fix it if possible, and keep what works as options
that are off by default.

## How it was built (tests first)

1. `dqn.shaping` and `dqn.shaping_on_bump`: potential-based shaping in training only.
2. `train_step_limit_factor`: a training step limit; scoring stays at 4 x.
3. `stages`: size curriculum (experimental).
4. G4 (own card).
5. Loader: untimed warm-up call before the timed test run.
6. `policy_epsilon`: seeded random moves when playing (arena and scoring).
7. Every option recorded in `config.json` and the `.onnx` metadata (`training`).
8. Research write-up, example config, TRAINING.md section.
9. Research scripts in `scripts/research/` (no results data).

## Report

- **Result:** shaping takes size 9 from 0% to 69% +/- 10% on test (8 seeds); the best brain on
  validation rescues collapsed runs (0% -> 62% and 64%); 10% random moves when playing gives 83%
  on test with 1.36 x longer routes. Curriculum hurt; Enb no gain on validation; size 11 still
  fails (8%). Details: `docs/research/2026-11-23-dqn-shaping.md`.
- **Defaults:** every new option is off by default, except best-on-validation export with pools
  (G4), which the repo owner chose as the default.
- **Flaky test fixed:** `tests/test_cli.py::test_check_brain_and_play_with_brain` failed now and
  then on a cold first run; the loader's first call is now untimed.
- **Left:** visit counts as input (obs_version 2), PPO, a memory brain, choosing the random-move
  rate on validation, size 11.
- **Lessons:** see LESSONS.md (2026-11-23, DQN research).
