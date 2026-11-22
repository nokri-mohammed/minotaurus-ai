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
