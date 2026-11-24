# G25: Run all levels

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** server, web, contract
- **Model:** opus
- **CEO go:** 2026-11-24 ("yes do all of them, do not push until I test them locally")

## Report

- **Done:** `POST /api/brains/{id}/run-all` plays all 19 portal levels (7 hand-made, 12 test
  samples) at full speed with the same seed as a run by hand, so a level gives the same result both
  ways; the batch is saved in `var/arena.db`. `GET /api/brains/{id}/batches` lists a brain's earlier
  batches. The Arena has a "Run all levels" button and an "All levels" panel: "12 of 19 finished
  (63%)", hand-made and test counts, a row per level, the percent of last time, and earlier runs.
  Contract in step (Pydantic, JSON Schema, zod, samples).
- **Check on the real wide brain (seed 4):** 12 of 19 finished in 0.2 s.
- **Tests:** pytest and bun test pass; build clean.
- **Not seen:** the page in a browser.
- **Left:** the Brains page with comparing (G26). The mock (`web/mock/`) has no run-all.
