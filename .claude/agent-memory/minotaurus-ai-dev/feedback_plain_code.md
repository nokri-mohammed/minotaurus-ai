---
name: feedback-plain-code
description: CEO rule for minotaurus-ai: write plain step-by-step code, no compact comprehensions or one-liners
metadata:
  type: feedback
---

Write plain, readable code: explicit `for` loops with named steps, not compact comprehensions, generator expressions inside `tuple(...)`, or one-line tricks.

**Why:** CEO rule, 2026-11-22, said "never compact, simplify this" about `by_id = {level.id: level for level in levels}`. The CEO is learning the code and reads it line by line.

**How to apply:** all new and edited Python and TypeScript in this repo. Prefer `for` + `append` / assignment over comprehensions, `map`/`filter` chains and nested ternaries; name intermediate values; add a short comment on why. When touching old code, fix the lines you touch. Related: [[feedback-async-await]].
