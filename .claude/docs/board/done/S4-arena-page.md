# S4: arena page

- **Owner:** minotaurus-ai-dev
- **Area:** web
- **Model:** sonnet
- **Design:** ../../plans/minotaurus-ai.md, "MVP scope change", stage 4; how-to in the card below

## Goal

One page on 127.0.0.1: load a brain, pick a level, watch the run (dot, trail, steps, timer), see the
result (time and steps, or timed out), and see every past attempt (kept in `localStorage`). React
with React Aria Components; logic in plain TypeScript modules. The server (S3) is not built yet:
the page talks to it through a fixed message contract and has a built-in mock (`?mock=1`).

## Scope

- Do: `data/schemas/messages.schema.json` (the contract S3 will implement), protocol, history, run
  reducer, drawing, API client plus mock, Arena page, tests (`bun test`).
- Do not: touch the Python server, the P1 race page, add ajv or other new libraries.

## Done when

`bun test`, `bun run typecheck`, `bun run build` pass; with `uv run minotaurus dev` and
`http://127.0.0.1:5173/?mock=1` the CEO runs a brain, sees a finish and a timeout, reloads and
still sees all past attempts.

## Report

### What I did

- `data/schemas/messages.schema.json`: the contract S3 must implement (WS `/ws/run?level_id=` sends
  `run_started`, `tick`, `result`, `error`; `GET /api/levels` returns id, name, difficulty, grid,
  step_limit; `POST /api/brain` (field `file`) returns name and method). Checked by
  `tests/test_messages_schema.py`.
- `web/src`: `protocol.ts` (types and message parser), `history.ts` (localStorage attempts, safe
  when storage is blocked), `run.ts` (pure reducer), `draw.ts` (canvas), `net.ts` (real API and
  `?mock=1` mock), `Arena.tsx` (React Aria `FileTrigger`, `Select`, `Button`, `Table`), `App.tsx`.
- Mock (`?mock=1`): two levels, one finishes in 13 steps, one has a 6-step limit and times out.
- 10 bun tests written first (red), then green.

### Test output

```
$ bun test            10 pass, 0 fail
$ bun run typecheck   clean
$ bun run build       built
$ uv run pytest       54 passed (Python), ruff clean
```

### How to check

`cd web && bun install`, `uv run minotaurus dev`, open http://127.0.0.1:5173/?mock=1, press **Load
brain** (any file ending `.onnx`), **Start run**; pick the "times out" level for the other result;
reload and the attempts are still listed.

### What is left

- S3 must serve this contract; until then only `?mock=1` works (without it the page says the
  server is not reachable).
- Not tested in a real browser by me; the CEO checks by looking.
- Page sends the file only; the brain's real method and name come from S3's upload reply.
- New dev-only dependency: `@types/bun` (types for `bun test`).
- P1 race page (lobby, two dots, replay) is not part of this card.

### Lessons

- The message parser is hand-written (no ajv), so the schema and the parser can drift; the Python
  test checks the schema, `protocol.test.ts` checks the parser, S3's tests must check the real
  server against the schema.
- Keep logic out of components: the reducer, history and parser are tested without a browser.
