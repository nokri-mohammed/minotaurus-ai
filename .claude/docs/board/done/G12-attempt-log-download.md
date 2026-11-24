# G12: download a log of each attempt

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** web
- **Model:** opus
- **CEO go:** 2026-11-24

## Goal

Each row in "Past attempts" has a Download button. It saves a JSON file with what the brain did,
step by step, with the time of each step.

## How to build it (tests first)

1. `services/attemptLog.ts`: `buildAttemptLog(attempt)` turns the saved path into the file content
   (one entry per step: `n`, `x`, `y`, `seconds`, `move`); `downloadAttemptLog(attempt)` saves it.
2. `services/history.ts`: an attempt can carry its `path` (a list of [x, y]); only the newest 30
   attempts keep it, so the browser storage stays small. Older saved attempts still load.
3. `Arena.tsx`: save the path with the attempt; a "Log" column with the Download button.
4. No server change and no contract change. What the brain saw and its scores per step stay in
   the backlog (G5).

## Report

- **Done:** `services/attemptLog.ts` (`buildAttemptLog`, `logFileName`, `downloadAttemptLog`); attempts
  carry an optional `path` (newest 30 keep it, older saved attempts load as before); a "Log" column
  with a Download button on each past attempt that has a path. The file has `format`, `version`,
  `step_seconds`, the attempt summary and one entry per square: `n`, `x`, `y`, `seconds`, `move`
  (`up`, `down`, `left`, `right`, `blocked` for a wall bump).
- **Tests:** `bun test` 52 passed, typecheck and build clean. Python untouched (352 passed).
- **Left:** I have not clicked the button in a browser. Attempts made before this change have no
  path, so they show a dash. What the brain saw and its 4 scores per step is still G5 (needs the server).
- **Lessons:** in LESSONS.md.
