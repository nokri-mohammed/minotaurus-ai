---
name: feedback-async-await
description: CEO rule for minotaurus-ai code: always async/await with try/catch, never promise chaining (.then/.catch/.finally)
metadata:
  type: feedback
---

Write async code with `async`/`await` and `try`/`catch`. Never use `.then()`, `.catch()` or `.finally()` chaining.

**Why:** CEO rule, 2026-11-22, after seeing `api.levels().then(...)` in `web/src/Arena.tsx`. Chaining reads worse and splits error handling from the call.

**How to apply:** every TypeScript or Python change in this repo, including new components and tests. In a React `useEffect`, define an inner `async function` and call it with `void fn()`; keep the cleanup return outside it. Before finishing a card, `grep -rn "\.then(\|\.catch(" web/src` should find nothing.
