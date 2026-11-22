# Team

```mermaid
flowchart TD
  CEO[CEO: approvals, starts each card] --> CoS[Chief of staff: plan, board, routing]
  CoS --> Dev[minotaurus-ai-dev, sonnet: whole repo]
  CoS -. post-MVP .-> IT[homelab-it: hosting, tunnel, IP allowlist]
  CoS -. post-MVP .-> Sec[security-specialist: review before the gate opens]
```

## Involvement log

| Date | Who | What |
|---|---|---|
| 2026-11-21 | chief of staff | design with EGM (Overview, Technical Plan, Alternatives, Implementation); skeleton; board |
| 2026-11-21 | minotaurus-ai-dev | S1: schemas, easy-01, engine (levels, observe, MazeEnv, Race), `play`, 43 tests |
| 2026-11-21 | minotaurus-ai-dev | web: React + React Aria hello world, `minotaurus dev`, backlog S4 updated (CEO decision) |
| 2026-11-21 | minotaurus-ai-dev | S4: arena page (React Aria), messages contract, mock mode, 10 bun tests |
| 2026-11-21 | minotaurus-ai-dev | web: restyle with design-taste-frontend (achromatic-ledger), RAC component set in `web/src/components/` |
| 2026-11-22 | minotaurus-ai-dev | S2: trainer (Q-table, DQN), ONNX export, safe brain loader, `check-brain`, `play --brain`, 77 tests |
| 2026-11-22 | minotaurus-ai-dev | S3: local arena server (messages, run loop, levels, upload, WebSocket run), training graph, TRAINING.md, backlog G1 to G5, 117 tests |
| 2026-11-22 | minotaurus-ai-dev | W1: confetti on a finish, progress charts (steps per run, outcomes), 33 bun tests |
| 2026-11-22 | minotaurus-ai-dev | web: maze drawn as thin wall lines (`wallLines` in draw.ts), 37 bun tests |
