# Board

| Column | Meaning |
|---|---|
| `todo/` | pulled from `BACKLOG.md` by the CEO, ready to start |
| `doing/` | being worked on (one card at a time) |
| `done/` | finished, with a `## Report` |
| `blocked/` | waiting for something; the card says what |

A card is one Markdown file named `<id>-<short-name>.md`, for example `S1-engine.md`. Move the file
to change its column (`git mv`). Card template:

```markdown
# S1: <title>

- **Owner:** minotaurus-ai-dev
- **Area:** engine | trainer | server | web
- **Model:** sonnet
- **Design:** ../../plans/minotaurus-ai.md, section <name>

## Goal
## Scope (do / do not)
## Done when
## Report
```
