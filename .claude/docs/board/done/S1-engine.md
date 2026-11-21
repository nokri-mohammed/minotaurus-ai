# S1: engine, schemas and first level

- **Owner:** minotaurus-ai-dev
- **Area:** engine
- **Model:** sonnet
- **Design:** ../../plans/minotaurus-ai.md, Detailed Implementation Plan, stage 1

## Goal

Level and config schemas, levels/easy-01.json, engine (levels, observe v1, MazeEnv, Race) with tests; `minotaurus play` moves a random dot in the terminal.

## Done when

See the stage table in the design ("The CEO can check" column).

## Report

### What I did

- Schemas: `schemas/level.schema.json`, `schemas/brain-config.schema.json` (qtable and dqn blocks,
  `observation.window` and `dqn.memory` reserved: anything but 5 / 0 is rejected).
- `levels/easy-01.json` (9 x 9, dead ends, exit on the east edge, shortest path 13, step limit 52).
- Engine in `minotaurus/engine/` (the path in CLAUDE.md, not `minotaurus/levels.py` as the design
  item list says): `levels.py` (load, validate, BFS, step limit 4 x shortest path), `observe.py`
  (obs_version 1, 77 floats), `env.py` (MazeEnv, rewards +1 / -0.01 / -0.05), `race.py` (two dots,
  draw, step limit, move log, brains as plain functions), `render.py` (text drawing).
- `minotaurus play [--level] [--seed] [--delay] [--max-steps]`: random dot in the terminal.
- 43 tests, written first (red: import error), then green.
- New dependencies: `gymnasium`, `numpy` (in the design) and `jsonschema` (to check the schemas;
  not named in the design, tell me if you want it replaced).

### Test output

```
$ uv run pytest -q
43 passed, 1 warning in 0.37s     (warning: starlette TestClient wants httpx2, from the skeleton)
$ uv run ruff check
All checks passed!
```

### What is left

- `messages.schema.json` and `examples/*.json` belong to later cards (S3, S2).
- `play` supports only the random brain until S2 adds ONNX loading.
- `schemas/` and `levels/` are found relative to the repo root; fine for `uv run`, must be packaged
  into the wheel or Docker image later.
- Race ends at the first finish; the design does not say whether the loser keeps going, so I chose
  "race over".

### Lessons

- The design's file list (`minotaurus/levels.py`) and CLAUDE.md (`minotaurus/engine/`) disagreed;
  CLAUDE.md won. Fix the plan text when the plan is next edited.
- Writing the window geometry tests with a hand-computed layout caught nothing wrong but pins
  `obs_version` 1: any future change to the layer order will fail loudly.
