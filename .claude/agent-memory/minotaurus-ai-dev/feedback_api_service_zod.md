---
name: feedback-api-service-zod
description: CEO rule for minotaurus-ai web: all server calls go through an ApiService class and every reply is validated with zod schemas
metadata:
  type: feedback
---

Web code reaches the game server only through `web/src/services/ApiService.ts` (a class, dependencies injectable), and every HTTP reply and WebSocket frame is validated with zod schemas defined in `web/src/protocol.ts`. No bare `fetch` or `new WebSocket` in components, no hand-written parsers or `realApi` object literals.

**Why:** CEO preference, 2026-11-22, after seeing `export const realApi: Api = {...}` and a hand-written message parser. Schemas give one definition of the contract and clear errors.

**Layout (CEO, 2026-11-22):** `ApiService` is generic (get, post, socket: base URLs, errors, zod validation). Each endpoint is its own file in `web/src/services/endpoints/` that calls it; `services/index.ts` exports `arenaApi`.

**How to apply:** any new endpoint adds a zod schema in `protocol.ts`, a new file in `services/endpoints/` with its own test (fake `fetchFn` or `openSocket`), an entry in `arenaApi`, and samples in `data/schemas/message-samples.json` (also checked by pytest against `messages.schema.json`). Related: [[feedback-async-await]].
