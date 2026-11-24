# G2: better metrics

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** trainer, server
- **Model:** opus
- **Rule from the CEO:** extend Mo's work, change nothing already there; ask before any refactor.

## Goal

See wandering and compare brain sizes.

## Report

- **Done (extension only, no refactor):**
  - `metrics.jsonl` training lines gain `avg_path_ratio` (steps / shortest path on finished tries,
    `null` when none finished) and `parameters`.
  - `parameter_count(agent)` in `export.py`; the `.onnx` metadata gets `parameters`.
  - The arena `result` gets an optional `path_ratio` (finished runs only): `Result` model, zod
    schema, `messages.schema.json` and the shared samples.
- **Tests:** `uv run pytest` 302 passed, ruff clean; `bun test` 37 passed, typecheck clean.
  Real run (qtable-brain, easy-01, 3000 tries): path ratio 1.057, parameters 1580, same number in
  the `.onnx` metadata.
- **Left:** the page does not show the path ratio yet; the training graph has no panel for it.
  Both are small and not in this card.
- **Lessons:** in LESSONS.md.
