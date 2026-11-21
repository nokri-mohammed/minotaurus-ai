# Backlog

Everything that needs doing, not started. The CEO says which items to pull into Todo on the
boards: [Python](board/python.md), [Web](board/web.md). Card details: `.claude/docs/board/`.

## Python (engine, trainer, server)

- **S2** trainer: Q-table and DQN, ONNX export, `check-brain`
- **S3** local arena server: upload a brain, run it with timeout and timer, stream ticks
  (web side: S4)
- **P1** (after MVP) live online 1v1: rooms, two players
- **P2** (after MVP) online, gated to two IP addresses, security review

## Web (page)

- **S4** arena page: load a brain, pick a level, watch the run, attempt history in the browser
  (needs S3)
- **P1** (after MVP) race page for two players
