# G19: steadier wide example

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** trainer (example config, docs)
- **Model:** opus
- **CEO go:** 2026-11-24 ("yes")

## Report

- **Done:** `data/examples/dqn-mixed-wide-stable-brain.json`: the wide example with `learning_rate`
  0.0003 (was 0.001) and `target_update` 1000 (was 200); the same mazes, recipe, seeds and
  early stop. A test checks that only those two settings differ. TRAINING.md records the wide run.
- **Not run by me:** the CEO runs it: `uv run minotaurus train --config data/examples/dqn-mixed-wide-stable-brain.json`.
  Time: about the same as the wide run (39 min), longer if it no longer collapses and trains on.
- **Left:** the run. It is a guess that these two settings steady it; two changes at once, so a good
  result will not say which one helped.
- **Lessons:** in LESSONS.md.
