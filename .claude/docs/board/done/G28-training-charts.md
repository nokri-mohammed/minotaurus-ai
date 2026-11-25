# G28: training graph drawn in the page (shadcn charts)

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** server, web
- **Model:** opus
- **CEO go:** 2026-11-25 ("can we recreate training graph? use shadcn library instead?")

## Report

- **Done:** `GET /api/brains/{id}/metrics` (Pydantic `BrainMetrics`, JSON Schema, samples, zod) reads
  `metrics.jsonl` from the bundle: training points, quiz checks and the saved try. The Recipe panel's
  "Training graph" now draws five shadcn line charts (success rate with the quiz, steps, points,
  random moves, error) with a dashed line at the saved try. New dependency: `recharts` (via the
  shadcn `chart` component).
- **Tests:** pytest 424 passed, ruff clean; `bun test` 77 passed, typecheck and build clean.
- **Not seen:** the charts in a browser.
- **Left:** the `graph.png` endpoint and the PNG in the bundle are kept (nothing in the page uses
  them now). The page bundle is about 910 kB (recharts), fine for a local arena.
- **Lessons:** see LESSONS.md (read only the fields you declare).
