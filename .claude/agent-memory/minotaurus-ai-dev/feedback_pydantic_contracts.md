---
name: feedback-pydantic-contracts
description: CEO rule for minotaurus-ai Python: data contracts (config, server messages) are Pydantic models, the twin of the web's zod schemas
metadata:
  type: feedback
---

Python data contracts are Pydantic models (strict, `extra="forbid"`), not loose dicts or hand-checked JSON.

**Why:** CEO preference, 2026-11-22, after asking for "something like zod for Python". Same idea as the web side ([[feedback-api-service-zod]]).

**How to apply:** training config already done (`minotaurus/trainer/config.py`); the S3 server messages (`run_started`, `tick`, `result`, `error`, level list, brain reply) must be Pydantic models, with `data/schemas/message-samples.json` as the shared test against the zod side. Schema JSON files are generated from the models, with a drift test. Level files still use `jsonschema` until someone moves them.
