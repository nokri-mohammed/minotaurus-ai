# Research scripts (2026-11-23, DQN on generated mazes)

The scripts behind [docs/research/2026-11-23-dqn-shaping.md](../../docs/research/2026-11-23-dqn-shaping.md)
and [docs/research/2026-11-23-official-brain.md](../../docs/research/2026-11-23-official-brain.md) (`official_*`).
Run them from the repository root with `uv run python scripts/research/<script>.py`. Results go to
`runs/research/` (git-ignored); no results are committed.

| Script | What it does |
|---|---|
| `run.py RUN SEED` | trains one research run and scores it: `result.json` with the `evaluate.py` success rates, steps, steps / shortest path, ties, bumps and loops on train, validation and test, a seeded random player on test, the share of training tries that reached the exit in the first 500, and the training CPU seconds |
| `checkpoint_sweep.py RUN_DIR` | scores every checkpoint (every 500 tries) on validation, keeps the best (a tie keeps the later one), scores it on test |
| `eps_eval.py RUN_DIR --name NAME` | scores a brain with random-move rates 0, 0.02, 0.05 and 0.1 when playing, seeded, 5 repeats |
| `maze_counts.py` | different mazes per size (5, 7, 9) and how often a random walk finds the exit within the step limit |
| `common.py` | the runs table, the pools and the scoring helpers |
| `official_train.sh` | trains the official brain: `data/examples/dqn-shaped-brain.json` with seeds 1 to 8 in parallel, CPU only, into `runs/official-dqn-shaped/`, and prints the wall time |
| `official_select.py` | ranks those seeds on VALIDATION only (success, then fewer mean steps) and prints the winner; never plays the test mazes |
| `official_eval.py RUN_DIR` | the winner only: TEST with `policy_epsilon` 0 and 0.05, and one arena run on easy-01, easy-02, medium-01, medium-02 |
| `official_trace.py BRAIN` | traces on all 6 hand-made levels: shortest path, greedy run with bumps in a row and where, success with `policy_epsilon` 0.05 and 0.1 (200 seeded tries), and a greedy run that never moves into a visible wall |

## Runs

`RUN` is one of the runs in the write-up (pools: A = size 9, 222 / 50 / 50; B = size 11,
222 / 100 / 100; C = size 11, 500 / 100 / 100; all `maze_seed` 1, 5000 tries):

| Run | Options on top of `data/examples/dqn-brain.json` |
|---|---|
| A, B, C | none (pools A, B, C) |
| D | `train_step_limit_factor` 20, `epsilon_decay` 0.999 |
| E | `dqn.shaping` |
| F | D + E |
| G | F + `stages` [5, 7, 9] |
| E11 | E on pools B |
| Enb | E with `dqn.shaping_on_bump` false |

The research exported the last brain, so these configs set `eval_every` to 0; use
`checkpoint_sweep.py` for the best one, or train with the default (`eval_every` 250).

Example, the three E seeds and their random-move scores:

```sh
for seed in 1 2 3; do uv run python scripts/research/run.py E $seed & done; wait
for seed in 1 2 3; do uv run python scripts/research/eps_eval.py runs/research/E-s$seed/run --name E-s$seed; done
```

## Notes

- One run takes 12 minutes (E) to 100 minutes (D) of one CPU core. Each run uses one torch
  thread, so several can run side by side, one per core.
- Scoring uses a 1 s per-step time limit in the loader instead of 0.05 s, because many runs at
  once share the CPU (`SCORE_TIME_LIMIT_S` in `common.py`). Scoring only; the repo default is
  unchanged.
- The same seed gives the same run: `run.py E 1` reaches the exit in 49.4% of its first 500
  training tries, as in the write-up.
