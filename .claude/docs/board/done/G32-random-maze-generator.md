# G32: random maze generator in the Arena

- **Owner:** minotaurus-ai-dev (the lead), working now (CEO go: 2026-11-25 "ok go build that")
- **Area:** server, web
- **Model:** sonnet
- **Asked by the CEO:** 2026-11-25 ("select difficulty/size, then a generate button")

## What

In the Arena the CEO picks a **difficulty** and a **size**, presses **Generate**, and gets a fresh
random maze to watch the selected brain on. It is not saved and not part of any score.

## How

- **Engine:** `generate_maze(seed, size, random_start, border_exit)` already exists. Difficulty follows
  size (`_difficulty_for`: easy up to 9, medium up to 17, hard above), so the difficulty picker only
  limits the sizes offered: easy 5 to 9, medium 11 to 17, hard 19 to 41 (odd sizes only).
- **Server:** `POST /api/mazes/random` with `{size, seed?}`; no seed means the server draws one. The reply
  is a `LevelInfo` (Pydantic model, JSON Schema, sample and zod in step) with the seed in the id
  (`gen-<size>-<seed>`), so the same seed gives the same maze. The run socket accepts such a level id.
- **Web:** controls next to the Level select: Difficulty, Size (filtered by difficulty), a Generate
  button. The new maze is shown as the selected level (title strip, e.g. `GEN-13-4821 13X13`) and runs
  with the normal Start button. An endpoint file in `services/endpoints/`, zod in `protocol.ts`.
- **Not saved:** a run on a generated maze is only for watching (CEO rule 2026-11-25). Run all levels
  stays the fixed 19 levels so ratings remain comparable.

## Decisions taken (CEO had not answered; easy to drop)

- Both tick boxes ("Exit in the outer wall", "Random start") and an optional Seed box are in.

## Done means

pytest for the endpoint (valid sizes, refused sizes, same seed same maze), `bun test` for the size
list per difficulty, typecheck and build clean, card report with lessons, README line.

## Report

- **Done:** `generated_level_from_id` rebuilds a maze from its id. `POST /api/mazes/random`
  (`RandomMazeRequest`, strict Pydantic; size odd 5 to 41, seed 0 to 999999 or drawn) returns a
  `LevelInfo` with `group: "random"`. The run socket accepts a generated id. The Arena has a
  Random maze panel (Difficulty, Size, Seed, two tick boxes, Generate); the new maze replaces any
  earlier random one in the level list and is selected. Contracts updated: Pydantic, JSON Schema,
  samples, zod.
- **Tests:** pytest 478 passed (id round trip, same seed same maze, refused sizes, run by id);
  `bun test` 87 passed; typecheck, build and ruff clean. Not seen in a browser.
- **Left:** `dev --mock` has no random maze endpoint. The LED board resizes to the biggest maze in the
  list, so a size 41 maze makes every maze smaller until it is replaced. No save, no score (as asked).
- **Lessons:** see LESSONS.md.
