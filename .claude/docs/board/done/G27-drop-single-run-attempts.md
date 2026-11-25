# G27: drop single-run attempts, per-level results on the Brains page

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** server, web
- **Model:** opus
- **CEO go:** 2026-11-25 ("agreed", after the plan: stop saving manual runs, make the batch the record, delete History and the attempts table and API)

## Report

- **Done:** removed `GET/POST /api/attempts`, `/api/attempts/import`, the `AttemptRecord` model, the
  `attempts` table creation, its schema defs and samples, and their tests. Web: removed the History
  page, attempt history and log code, the progress charts and the past-attempts panel; `#history`
  now opens the Arena. A manual run is only for watching. The Brains page has a "Levels of brain"
  Select and the All levels panel (Run all levels, per-level results, earlier runs).
- **Tests:** `uv run pytest` 419 passed, `ruff check` clean; `bun test` 69 passed, typecheck and build
  clean.
- **Not seen:** the pages in a browser.
- **Left:** an existing `var/arena.db` keeps its old `attempts` table, unused (nothing reads or
  drops it). Replay of a past run is not built (batch results do not store the path; it would make
  batches much bigger). The BatchPanel still sits under the Arena split.
- **Lessons:** see LESSONS.md (do not store what a batch already says).
