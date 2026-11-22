---
name: feedback-api-service-zod
description: CEO rule for minotaurus-ai web: all server calls go through an ApiService class and every reply is validated with zod schemas
metadata:
  type: feedback
---

Web code reaches the game server only through `web/src/ApiService.ts` (a class, dependencies injectable), and every HTTP reply and WebSocket frame is validated with zod schemas defined in `web/src/protocol.ts`. No bare `fetch` or `new WebSocket` in components, no hand-written parsers or `realApi` object literals.

**Why:** CEO preference, 2026-11-22, after seeing `export const realApi: Api = {...}` and a hand-written message parser. Schemas give one definition of the contract and clear errors.

**How to apply:** any new endpoint adds a zod schema, a method on `ApiService`, a test with a fake `fetchFn`, and samples in `data/schemas/message-samples.json` (also checked by pytest against `messages.schema.json`). Related: [[feedback-async-await]].
