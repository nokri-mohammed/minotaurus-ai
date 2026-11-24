# G21: drop the steps column

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** trainer, cli
- **Model:** opus
- **CEO go:** 2026-11-24 ("then drop those not useful metrics")

## Report

- **Done:** the several-seeds table has no `steps` column; `path`, `saved at`, validation, test,
  hand-made and time stay. `test_steps` and `avg_steps` are still in `summary.json`. TRAINING.md updated.
- **Tests:** `uv run pytest` passed, ruff clean.
- **Left:** the CEO also liked renaming `hand-made` to `portal` (dropdown: Portal levels, Exam
  samples) and a per-size breakdown; not started, waiting for the go.
- **Lessons:** in LESSONS.md.
