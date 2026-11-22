# minotaurus-ai

Train a maze brain with reinforcement learning (Q-table or DQN), export `.onnx`, run it in a
local arena (MVP); race two brains online later. Design: `.claude/docs/plans/minotaurus-ai.md`. Team rules:
`~/projects/assistants/homelab-team-all/CLAUDE.md`.

## Rules

- One copy of the game rules: `minotaurus/engine/`. The trainer imports it; the server wraps it;
  the web page only draws.
- Brain input contract: `obs_version` 1 (5 x 5 window: walls, exit, visited; plus exit direction;
  77 numbers in, 4 scores out). Changing it means a new version.
- Uploaded `.onnx` files are untrusted: size limit, operator allowlist, shape checks, time limit.
- MVP = a local single-player arena on 127.0.0.1 (load a brain, run with timeout and timer, attempts
  saved in the browser). The online 1v1 race is post-MVP: internet access gated to two IP addresses
  first (values never in the repo), public later after a security review.
- One stage at a time, only on the CEO's word. Work is tracked on the board below.
- Async code: always `async`/`await` with `try`/`catch`, never promise chaining (`.then()`,
  `.catch()`, `.finally()`) in TypeScript, and the same in Python (`await`, no callbacks).
- No em dashes. No private values. Conventional Commits, noreply email, no co-author.

## Board

`BACKLOG.md` (root) holds every item not started, with how to build it. `minotaurus/BOARD.md` and
`web/BOARD.md` are the kanbans (Todo, Doing, Done, Blocked) per layer. The CEO pulls items from the
backlog into Todo: the item is cut from `BACKLOG.md` into a card file in
`.claude/docs/board/todo/`. Keep the pages in step whenever a card moves.

Cards: `.claude/docs/board/{todo,doing,done,blocked}/`: one card (Markdown file) per task, with an
`Area:` line (engine, trainer, server, web, or several). Move the
file to change its column; never copy it. A card in `doing/` names who works on it; a card in
`blocked/` says what it waits for. Finished cards get a `## Report` with lessons.

## Commands

- `uv sync`, `uv run pytest`, `uv run ruff check`, `uv run minotaurus hello|train|serve`
- `.taste-skill/` and `web/dist/` are build output, git-ignored
- `uv run minotaurus dev` starts the server and the page together (page on 127.0.0.1:5173)
- `cd web && bun install && bun run dev | build | typecheck | test`

## Team

Solo lead: `minotaurus-ai-dev` (`.claude/agents/minotaurus-ai-dev.md`).
