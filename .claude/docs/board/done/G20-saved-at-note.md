# G20: make "saved at" clear

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** trainer, cli
- **Model:** opus
- **CEO go:** 2026-11-24 ("can we add this to make it clear")

## Report

- **Done:** `saved at` shows `1250 of 3250` (the try out of the tries the run did, new field
  `tries_done` in `SeedResult` and `summary.json`); two lines under the table say the saved brain is
  the version with the best quiz (validation) score; TRAINING.md says the same.
- **Tests:** `uv run pytest` 362 passed, ruff clean.
- **Left:** the single-run output already says "exported the brain from episode N (validation X%)".
- **Lessons:** in LESSONS.md.
