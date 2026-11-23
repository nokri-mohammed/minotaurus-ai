# G1b: generator follow-up (random start, every-size overlap test, config guard test)

- **Owner:** Mo (rackiavic), from the `feat/procedural-levels` branch, rebased onto G1 (`5b1757b`)
- **Area:** engine, trainer (tests only)
- **Backlog:** builds on G1 in `BACKLOG.md`, already done. The old branch code (`generate_level`,
  `generate_split`) is dropped; this keeps upstream's `generate.py` and `pools.py`.

## Goal

Add the parts of the old branch that G1 does not have, without changing G1's default behaviour.

## Done when

`uv run pytest` and `uv run ruff check` pass; default pools are identical to G1's.

## Report

### What I did

1. **Cached schema validator:** `_validator` in `engine/levels.py` has `@cache`, so the level
   schema file is read once instead of on every `parse_level` (every generated maze goes through
   it). Test: two calls return the same object.
2. **Overlap test at every size:** for every odd size from 7 to 41, with and without random
   start, no wall layout is in two pools. Size 5 is left out: it has only 2 wall layouts, and a
   test checks that pools there are refused.
3. **Config guard test:** the `levels` field cannot reach validation or test mazes. The generated
   shape trains on the train pool only; a generated id cannot be named in the id list (it is not
   a level file); the difficulty shape only reads level files. No code change was needed.
4. **Random start, opt-in:** `generate_maze(seed, size, random_start=False)` and
   `build_pools(..., random_start=False)`. With it on, the start is a floor square picked by the
   seed after carving (same walls as the top-left maze of that seed), the exit is the square
   farthest from it, and the id ends in `-r`. Off by default: default pools are byte-for-byte the
   same as G1's (checked against upstream's `pools.py` on five settings).
   - Pools now skip a maze whose **walls** were already used (`walls(level)`), not its grid. With
     a fixed start this is the same thing; with random start it stops the same walls with another
     start from counting as a new maze.

### Measured

Distinct layouts in 20 000 seeds:

| Size | Walls | Grids with random start |
|---|---|---|
| 5 | 2 | 14 |
| 7 | 14 | 238 |
| 9 | 322 | 8526 |

A grid key with random start would have filled three "disjoint" 5 x 5 pools from 2 wall layouts.

Q-table example (`qtable-generated.json`, train 92%, validation 0%, test 0%): on validation 71% of
steps (1440 of 2024) and on test 61% (1312 of 2136) are views the table never saw. The exported
`.onnx` gives `[0, 0, 0, 0]` for each, and `argmax` picks move 0 (up) every time; into a wall
the view does not change, so the brain stays stuck until the step limit.

### What is left

- Random start is not in the training config yet (`levels.generated` has no setting for it).
- Proposed, not built: break ties at random in the brain (for example among equal top scores),
  so an unseen view does not always mean "up". It touches the loader and the arena, so it needs
  a CEO decision.

### Lessons

See LESSONS.md (2026-11-23, generator follow-up).
