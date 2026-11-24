# G6: train several seeds in parallel

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** trainer, cli
- **Model:** opus
- **Rule from the CEO:** extend Mo's work, do not refactor it; ask before any refactor.

## Goal

One command trains the same recipe with several seeds, one run per CPU core, and keeps the best
brain by validation score (never by test).

## How to build it (tests first)

1. Config: optional `seeds` (a list) and `parallel` (a number). `ConfigFile.for_seed(seed)`.
2. `minotaurus/trainer/multi.py`: `run_seeds` (a process pool, results as they finish), `pick_best`,
   `default_parallel`, a results table.
3. CLI: `--seeds N` (N seeds counting up from the config `seed`) and `--parallel P` override the
   config; without either, `train` works exactly as before.
4. Output: `runs/<name>/<time>/seed-<n>/` per seed, `best-brain.onnx`, `summary.json`.

## Report

- **Done (extension only):** config `seeds` and `parallel` (optional), `ConfigFile.for_seed`,
  `trainer/multi.py`, CLI `--seeds` and `--parallel`, table, `best-brain.onnx`, `summary.json`,
  TRAINING.md section. The single-seed path is untouched.
- **Tests:** `uv run pytest` 315 passed, ruff clean. Real run: `train --config
  data/examples/qtable-brain.json --seeds 4` trained 4 seeds on 4 cores in 9.3 s and picked seed 3.
- **Left:** per-seed progress lines are not streamed (only "seed N done"); a seed run on a GPU or
  another machine is the remote card. Short runs gain little (start-up cost).
- **Lessons:** in LESSONS.md.
