# S3: local arena server

- **Owner:** minotaurus-ai-dev
- **Area:** server
- **Model:** opus (done by the lead, no sub-agent)
- **Design:** ../../plans/minotaurus-ai.md, stage 3; contract in `data/schemas/messages.schema.json`

## Goal

A server on 127.0.0.1: upload one brain, run it on a chosen level with a timeout and a timer, stream
ticks, send the result. It implements the contract the page (S4) was built against. Depends on S2
(`minotaurus/brain/onnx_brain.py`).

## How to build it (tests first)

1. **Messages** (`minotaurus/server/messages.py`): Pydantic models, the twin of the zod schemas.
   Tests check every sample in `data/schemas/message-samples.json` (valid pass, invalid fail).
2. **Run loop** (`minotaurus/server/arena.py`): `MazeEnv` plus the loaded brain; one tick per 100 ms
   at normal speed; timeout is the level step limit; game time = ticks x 0.1 s; a brain that errors
   or runs over 50 ms in a step ends the run with `error`.
3. **HTTP/WebSocket** (`minotaurus/server/app.py`): `GET /api/levels`, `POST /api/brain`
   (multipart, goes through `load_brain`), `WS /ws/run?level_id=`. One brain and one run at a time.
   Binds 127.0.0.1.
4. **Test client** (`tests/test_server.py`): upload a trained example, run, read ticks and one
   result; a bad upload is refused with a clear message.

## Scope

- Do: the server, its tests, the `serve` command wiring, delete `web/mock/` and the `dev:mock`
  script when the real server works with the page.
- Do not: rooms, two players, the online race (P1), the G cards.
- New dependencies: `python-multipart` (FastAPI needs it for file uploads) and `websockets`
  (uvicorn needs it to serve WebSocket). Both are implied by the design.

## Done when

`uv run pytest` and `uv run ruff check` pass; `uv run minotaurus dev` runs the page against the real
server: load a trained brain, see a finish and a timeout, and a refused bad file.

## Report

### What I did

- `minotaurus/server/messages.py`: Pydantic models for every message (`RunStarted`, `Tick`, `Result`,
  `ErrorMessage`, `LevelInfo`, `BrainResponse`), strict, the twin of the zod schemas. One test checks
  them against the same `message-samples.json` as the web tests.
- `minotaurus/server/arena.py`: `run_arena(level, brain, tick_seconds)` is an async generator that
  yields `run_started`, one `tick` per move, then one `result` (finished, timed_out or error). Game
  time is ticks x 0.1 s. A brain that raises, is too slow or picks a move outside 0 to 3 ends the run
  with an `error` result.
- `minotaurus/server/app.py`: `create_app(tick_seconds)` with `GET /api/levels`, `POST /api/brain`
  (reads at most 1 MB plus 1 byte, goes through `load_brain`, a refused upload keeps the old brain,
  errors are `{"message": ...}`), `WS /ws/run?level_id=` (one run at a time, errors for no brain or
  an unknown level, reset when the page disconnects). `/api/hello` stays.
- Dependencies added: `python-multipart` (FastAPI file upload), `websockets` (uvicorn WebSocket).
- Tests first: 24 new tests in `test_server_messages.py`, `test_arena.py`, `test_server.py`.

### What I verified (real output)

- `uv run pytest`: 117 passed. `uv run ruff check`: clean.
- Real server (`uv run minotaurus serve`), `curl` and a real WebSocket client:
  - `GET /api/levels` returns `easy-01`.
  - Uploading a text file as `x.onnx` gives `{"message":"not a valid ONNX file: ..."}`.
  - A run with no brain gives `{'type': 'error', 'message': 'Load a brain (.onnx) first.'}`.
  - A trained Q-table uploads as `{"name":"qtable-easy","method":"qtable"}` and a run gives 15
    messages (start, 13 ticks, result): `{'status': 'finished', 'steps': 13, 'seconds': 1.3}`.
  - After a page disconnects mid-run, the next run works (the one-run flag is reset).

### What is left

- **Not seen in a real browser by me:** the page against the real server. Check with
  `uv run minotaurus dev` and open http://127.0.0.1:5173.
- **Waiting for the CEO's go (deleting files):** delete `web/mock/` and the `dev:mock` script and
  `dev --mock` option, as the plan says. I did not delete anything.
- Real time per tick is about 0.14 s, not 0.10 s (the sleep plus the brain and send time). Game time
  is counted in ticks, so results are exact; only the animation is a little slower than planned.

### Lessons

- A test run that goes green before the code exists is a sign the test is not testing the new thing
  (it happened once again with the `train()` signature earlier). Check that the first run is red for
  the right reason.
- FastAPI file upload needs `python-multipart` and a WebSocket server needs `websockets`: both are
  silent requirements of "FastAPI plus uploads plus WebSocket". Name them in the card up front.
- I deleted a test file out of habit and had to restore it: deleting needs the CEO's go, even for a
  test of an endpoint I wanted to remove.
- Keep the one-run flag in a `try/finally`, so a page that drops mid-run cannot lock the server.

