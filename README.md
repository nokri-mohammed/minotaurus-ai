<p align="center">
  <img src="web/public/icon.jpeg" alt="minotaurus-ai logo" width="200" />
</p>

# minotaurus-ai

Train a "brain" that solves a 2D maze with reinforcement learning (a Q-table or a neural network),
export it as an `.onnx` file, then run it in the arena and track your attempts. Later: race a
friend's brain online.

**Status:** skeleton only. Design: `.claude/docs/plans/minotaurus-ai.md`.

## Layout

```
minotaurus/            Python package
  engine/              the only copy of the game rules (levels, observe, MazeEnv, Race)
  trainer/             Q-table and DQN training, metrics, checkpoints, ONNX export
  brain/               safe loading of untrusted .onnx brains
  server/              FastAPI game server: rooms, uploads, race loop, WebSocket
  cli.py               `minotaurus hello | play | train | serve`
data/
  schemas/             JSON Schemas: level, brain config, messages
  levels/              maze levels (JSON, with difficulty)
  examples/            example brain configs (added in stage 2)
tests/                 pytest
web/                   TypeScript page (Bun, Vite): lobby, race, result; draws only
runs/                  training output (not committed)
```

## Run the skeleton

```sh
uv sync
uv run minotaurus hello          # CLI
uv run pytest                    # tests
uv run minotaurus serve          # server on http://127.0.0.1:8000/api/hello

cd web && bun install && bun run dev   # page on http://127.0.0.1:5173 (asks the server)
```

## Work board

`BACKLOG.md` lists what is not started, with how to build it; `minotaurus/BOARD.md` and
`web/BOARD.md` are the kanbans. Cards: `.claude/docs/board/`, one Markdown file per task in `todo/`,
`doing/`, `done/` or `blocked/`.
