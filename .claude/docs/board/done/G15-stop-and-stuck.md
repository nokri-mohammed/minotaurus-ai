# G15: stop button and auto-stop when stuck

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** server, web (contract change)
- **Model:** opus
- **CEO go:** 2026-11-24 ("add both 1 and 2")

## Goal

A run that loops no longer plays on until the step limit.

1. **Stop button** (page only): ends the run; the attempt is saved as "stopped".
2. **Auto-stop** (server): no new square for 100 steps ends the run with the new result status
   `stuck` and a message.

## How to build it (tests first)

1. `arena.py`: count the steps since the dot last reached a new square; `stuck_steps` (default
   100) ends the run. A timeout in the same step wins.
2. Contract: `Result.status` gains `stuck` in the Pydantic model, `messages.schema.json`, the zod
   schema and the shared samples. `stopped` is not a server status (an invalid sample).
3. Page: `AttemptStatus` = server statuses plus `stopped`; status pill, charts, history and the
   finding text know both; a Stop button; late messages after a stop are ignored.

## Report

- **Done:** (1) Stop button: ends the run, saves the attempt as `stopped` (a page-only status),
  late messages after a stop are ignored. (2) Auto-stop: `run_arena(stuck_steps=100)` ends a run
  with the new result status `stuck` and a message after 100 steps without a new square; a timeout
  in the same step wins. Contract: `stuck` in the Pydantic model, `messages.schema.json`, the zod
  schema and the samples (`stopped` is an invalid server status). The status pill, the outcome
  bars, the history check and the finding text know both statuses.
- **Tests:** `uv run pytest` 359 passed, ruff clean; `bun test` 57 passed, typecheck and build clean.
- **Left:** not clicked in a browser. Starting a new run within about 0.1 s of pressing Stop can get
  "A run is already in progress" (the server notices the closed socket on its next tick). The 100 is
  a guess; a brain with random moves might have escaped after 100 steps. Restart `uv run minotaurus dev`.
- **Lessons:** in LESSONS.md.
