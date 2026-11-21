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

## Report 2: restyle and components (CEO request, same day)

- Used the `design-taste-frontend` skill, app-screen run. Style dealt: `achromatic-ledger`
  (seed 63515402, light, no redraws). Chosen because the arena is a quick, repeated, one-person
  tool: chrome in ink, the one blue hue (#1d5fbf) only on the dot and its trail.
- Face: blue-grey ground (#f2f4f7) with white cards, light-grey maze walls so the dot carries the
  hue; the exit is a ink ring. Signature: the maze itself is the biggest block.
- The screen's question: "Did the brain get out, and how fast?" Answered by the maze, the finding
  line under the title ("Finished in 13 steps, 1.3 s.") and the two figures in "This run".
- React Aria Components now live in `web/src/components/`: `Button`, `FileButton` (FileTrigger),
  `Select`, `DataTable` (Table), `Panel`, `Stat`, `StatusPill`, `MazeCanvas`, `AppShell`. `Arena.tsx`
  only composes them. Added `summarize()` to `history.ts` (test written first).
- Gate: lint 0 FAIL (the one shadow WARN is the select popover, marked as allowed); inspect at
  1440, 768, 390: 0 FAIL, 1 WARN (`panel-void`: the empty attempts card has a blank band until the
  first run is saved; kept so the two columns end level). Looked at the desktop and phone shots.
- Bun tests 11 pass; typecheck and build clean; pytest 54 pass.
- Allowed deviations: Geist is named first in the font stack but not loaded (no font download, the
  page stays offline-friendly), so the system font shows.
- Not seen by me: the populated state (past attempts rows, result pill, trail), the tablet shot.
  The inspector cannot click; the CEO checks it with `?mock=1`.
- Lesson: no Chrome was found for the inspector; Playwright's Chromium in `~/.cache/ms-playwright`
  works through `CHROME_PATH`. `.taste-skill/` (inspector output) is git-ignored.
