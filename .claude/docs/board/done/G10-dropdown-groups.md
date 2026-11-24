# G10: group headings in the level dropdown

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** engine, server, web
- **Model:** opus
- **CEO go:** option 1 (2026-11-24). New optional `group` field in the level message.

## Goal

The level dropdown shows two groups, "Hand-made levels" and "Test mazes", each sorted from easy to
impossible.

## How to build it (tests first)

1. `load_portal_levels()`: hand-made levels sorted by difficulty, then test mazes sorted by difficulty.
2. Contract: `LevelInfo.group` = `"hand-made"` or `"test"` (default `"hand-made"`), in the Pydantic
   model, `messages.schema.json`, the zod schema and `message-samples.json`.
3. Server: `/api/levels` sets `group` from where the level came from.
4. Page: `Select` takes an optional `group` per option and draws a heading per group.

## Report

- **Done:** `load_portal_levels()` returns hand-made levels (easy to impossible) then test mazes
  (easy to impossible); `LevelInfo.group` (`hand-made` or `test`, default `hand-made`) in the Pydantic
  model, JSON Schema, zod and samples; `/api/levels` sets it; `Select` draws a heading per group
  (`groupOptions` helper, new CSS class `menu-heading`).
- **Tests:** `uv run pytest` 341 passed, ruff clean; `bun test` 42 passed, typecheck and build clean.
- **Left:** I have not looked at the dropdown in a browser. Restart `uv run minotaurus dev` (it has
  no reload) so the new order and headings show.
- **Lessons:** in LESSONS.md.
