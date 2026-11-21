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
