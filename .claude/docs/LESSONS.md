# Lessons

- **S1 (2026-11-21):** the plan's file paths (`minotaurus/levels.py`) disagreed with CLAUDE.md
  (`minotaurus/engine/`). CLAUDE.md wins; fix the plan when next edited.
- **S1:** tests that pin the exact observation layout protect `obs_version` 1; a layout change must
  bump the version.
- **S1:** the race rule "does the loser keep going?" was not in the design; chosen: the race ends at
  the first finish.
- **Web setup (2026-11-21):** `@vitejs/plugin-react` 6 needs Vite 8; with Vite 7 use plugin-react 5.
- **Dev check:** stop a started `minotaurus dev` with `timeout -s INT` (Ctrl-C path), not `pkill`; the
  Ctrl-C path shuts down both child processes.
- **S4 (2026-11-21):** build the page against a written message contract plus a mock; the server
  (S3) then implements the contract and its tests validate against `messages.schema.json`.
- **S4:** logic in pure modules (reducer, history, parser) keeps it testable with `bun test`.
- **Web style (2026-11-21):** for any UI work, load the `design-taste-frontend` skill first (app-screen
  run) and keep reusable pieces in `web/src/components/`; pages only compose them.
- **Inspector:** set `CHROME_PATH` to Playwright's Chromium (`~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome`).
- **S2 (2026-11-22):** a 77-number observation cannot be packed into one int64 as bits. Use a
  hashed key (`sum((obs + 1) * weight)`) computed identically in Python and in the ONNX graph.
- **S2:** onnxruntime int64 `ReduceSum` is exact only up to 2**53; keep integer keys below that,
  or Python and ONNX disagree. Always test "ONNX output equals in-memory brain".
- **S2:** torch CPU wheels: use an `explicit = true` uv index plus `[tool.uv.sources]` so numpy and
  other packages still come from PyPI. Export with `torch.onnx.export(..., dynamo=False)` to avoid
  the onnxscript dependency.
- **Code style (2026-11-22, CEO rule):** no promise chaining; use `async`/`await` with `try`/`catch` everywhere. Rule is in CLAUDE.md, the agent brief and agent memory.
- **Mock (2026-11-22, CEO decision):** the page has no mock code at all. A fake arena is a Vite plugin (`web/mock/arenaMock.ts`, mode `mock`: `bun run dev:mock`, `minotaurus dev --mock`) that serves the same contract (`/api/levels`, `/api/brain`, `WS /ws/run`) with a hand-written WebSocket handshake (no `ws` dependency). Delete `web/mock/` when S3 lands.
- **ApiService + zod (2026-11-22, CEO rule):** one `ApiService` class is the only place that fetches or opens a socket; zod schemas in `protocol.ts` validate every reply and WebSocket frame. `data/schemas/message-samples.json` is checked by pytest (JSON Schema) and bun (zod), so the two sides cannot drift. `ApiService` takes `fetchFn` and `openSocket` so tests use fakes.
- **Folders (2026-11-22, CEO rule):** services (`ApiService`, attempt `history`) live in `web/src/services/`, components in `web/src/components/`.
- **Endpoint files (2026-11-22, CEO rule):** `ApiService` is the generic core (get, post, socket, validation, errors); each endpoint is one file in `web/src/services/endpoints/` (`levels`, `brain`, `run`); `services/index.ts` re-exports the endpoint functions.
- **No service props (2026-11-22, CEO rule):** endpoint functions use the shared `apiService` themselves; components call `getLevels()`, `uploadBrain(file)`, `openRun(id, cb)` and pass only their own arguments. Endpoint tests stub the globals (`fetch`, `WebSocket`, `location`).
- **CLI (2026-11-22, CEO decision):** `minotaurus/cli/` uses Typer: one file per command with one typed function `run`; `__init__.py` registers them on `app`. Entry point `minotaurus = "minotaurus.cli:main"`. Tests use `typer.testing.CliRunner`. Dependency added: `typer`. A top-level `cli/` was tried and reverted: the name is too generic and code belongs inside the package.
- **Pydantic (2026-11-22, CEO rule):** the training config is Pydantic models in `minotaurus/trainer/config.py` (strict, `extra=forbid`); `jsonschema` stays only for level files. The brain-config JSON Schema file is generated from the models. S3's server messages will be Pydantic models too, checked against `message-samples.json`.
- **Lean Pydantic (2026-11-22):** no wrapper layers around a model: no custom error class, no dataclass forwarding properties, no message reshaping. Use `Model.model_validate(_json)` and let `ValidationError` speak (it lists every wrong setting at once). Put small helpers on the model (`resolve_levels()`, `params`). Typer's `exists=True` handles a missing file.
- **Plain code (2026-11-22, CEO rule):** no compact comprehensions or one-line tricks; explicit loops with named steps. Applied to the level functions; older code is fixed when it is touched.
- **S3 server (2026-11-22):** messages are Pydantic models checked against the shared samples; the run loop is an async generator (`run_arena`), no callbacks; one-run flag reset in `try/finally`; errors reach the page as `{"message": ...}`. FastAPI uploads need `python-multipart` and WebSocket needs `websockets`. Never delete a file without the CEO's go (a test file was deleted and restored).
- **Animation and charts (2026-11-22):** keep the maths in pure functions (`stepPieces`, `layoutLine`) with bun tests; the canvas and SVG are thin. No library for confetti or charts. Respect `prefers-reduced-motion`. A static render plus headless Chrome screenshot checks a chart when nothing can click.
- **Thin maze walls (2026-11-22, CEO request):** the grid stays blocks in the data; the page draws each wall cell as a point and joins touching wall cells with one thin line (`wallLines`, pure and tested). A gap in the outer wall stays a gap. Works for any grid, not only room-and-wall mazes.
- **More levels (2026-11-22, CEO request):** five perfect mazes made with a one-off depth-first script (not in the repo, G1 is the real generator); the seed with the longest shortest path was kept per size. `load_all_levels` orders easy, medium, hard, then id, and a test checks each shipped level has a longer shortest path than the one before. A brain trained on easy-01 does not solve the new levels: it memorised one maze (see G1).
- **Maze generator (2026-11-23, G1):** pools are drawn test first, then validation, then train, each skipping any layout already used, so no train maze is a test maze. The pool settings go into the `.onnx` metadata and scoring refuses a brain whose settings differ from the config. Size 7 has too few different mazes for 16 pools: ask for less or a bigger size (the code says so). Result with a Q-table, size 9, 50 train mazes, 6000 episodes: train 92%, validation 0%, test 0%. It memorises; a Q-table on raw 5x5 views does not generalise yet.
