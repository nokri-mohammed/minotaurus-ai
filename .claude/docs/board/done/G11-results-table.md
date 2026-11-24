# G11: results table shows the saved brain

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** trainer, cli
- **Model:** opus
- **CEO go:** 2026-11-24 ("update this table")

## Goal

The several-seeds table describes the brain that is saved, not the last training window.

## Report

- **Done:** `saved at` replaces `finished`; `steps` and `path` come from the saved brain on the test
  mazes (`playthrough_stats`, written to `test_stats.json`); `collapse_warnings` names a seed whose
  last validation check fell below half of its saved brain's; the new numbers are also in
  `summary.json`. Without made mazes the table falls back to the last training window.
- **Tests:** `uv run pytest` 352 passed, ruff clean (new `tests/test_seed_table.py`).
- **Left:** the single-run output was not changed; the `done` order column was not added.
- **Lessons:** in LESSONS.md.
