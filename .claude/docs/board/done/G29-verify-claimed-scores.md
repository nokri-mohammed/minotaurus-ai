# G29: the server re-checks a bundle's claimed scores

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** server, web
- **Model:** opus
- **CEO go:** 2026-11-25 ("ok publish changes then build 1 and 2")

## Report

- **Done:** `minotaurus/verify.py` regenerates the exam mazes from the bundle's `config.json`, plays
  the brain again (validation and test piles, the hand-made levels, the test steps and route) and
  compares with `scores.json`, `fixed_levels.json` and `test_stats.json`. It also refuses a brain
  trained on other mazes than the settings name (the pile-match check). `POST
  /api/brains/{id}/verify` runs it in a thread, one at a time, and keeps the answer in the
  `verifications` table. The Recipe panel shows a Verified / Scores do not match / Not checked badge
  with the numbers that differ. The training pile is not repeated (the slowest, 9 s on the wide run
  for all three piles; about 3 s without it) and the page says so.
- **Tests:** pytest 436 passed, `bun test` 80 passed, build clean. Tests change a score, a
  hand-made result and the maze seed and each is caught.
- **Not seen:** the badge in a browser.
- **Left:** a first check on a big bundle blocks that one call for a few seconds (no progress
  bar). The Brains table does not show the badge yet. Signing is G30.
- **Lessons:** see LESSONS.md.
