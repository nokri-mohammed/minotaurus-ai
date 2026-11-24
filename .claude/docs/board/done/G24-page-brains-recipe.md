# G24: the page: brain dropdown, attempts per brain, Recipe panel

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** web, contract
- **Model:** opus
- **CEO go:** 2026-11-24 ("yes do all of them, do not push until I test them locally")

## Report

- **Done:**
  - Contract in step: zod schemas (`brainInfoSchema` with id, `brainsSchema`, `brainRecipeSchema`,
    `attemptRecordSchema`, `attemptsSchema`) checked against the same samples as the Pydantic side.
  - Services: `getBrains`, `getBrainRecipe`, `brainGraphUrl`, `getAttempts`, `saveAttempt`,
    `importAttempts`; `openRun(levelId, brainId, cb)`; `ApiService.postJson`.
  - Arena: a Brain dropdown ("name (a3f9c21e)") next to Load brain (accepts `.onnx` and `.tar`);
    loading another brain gives a fresh page (its own attempts, charts and totals); the list comes
    from the server, so it survives a restart. A Recipe panel under the maze: grouped plain-word
    settings and result, a training graph toggle, Copy config; a plain `.onnx` says how to pack it.
  - History: a Brain filter ("All brains", one brain, "Unknown brain (older attempts)").
  - Attempts live in the server database; the ones an older page saved in the browser are imported
    once (`brainId` "unknown"). Attempt logs carry `brain_id`.
  - The fake-arena mock (`web/mock/`) follows the new endpoints, in memory.
- **Tests:** `bun test` 73 passed, typecheck and build clean. Smoke test: a real bundle uploaded to a
  real server, recipe and graph read back.
- **Not seen:** the page in a browser (the CEO tests it).
- **Left:** Run all levels (G25), the Brains page (G26).
