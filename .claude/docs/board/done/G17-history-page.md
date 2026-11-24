# G17: History page with all attempts and the log downloads

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** web
- **Model:** opus
- **CEO go:** 2026-11-24

## Goal

The Arena's "Past attempts" table was squeezed by the Download column. Move the downloads to a
full-page History table.

1. Arena: no Download column; the table shows only the newest 10 attempts, with a link to History.
2. New page **History** (sidebar link, `#history`): every saved attempt, a Download button per row,
   and a "Download all logs" button (one JSON file with every log).
3. Attempts are kept in `App` so both pages see the same list; the Arena stays mounted (hidden)
   so a run is not lost when you look at History.
4. Paths (the log data) are kept for the newest 100 attempts instead of 30, because the History
   page promises a log per row.

## How to build it (tests first)

`page.ts` (`pageFromHash`), `recentAttempts` in `history.ts`, `buildAllLogs` and
`allLogsFileName` in `attemptLog.ts`; then `History.tsx`, `AppShell`, `App`, `Arena`.
No server change and no contract change.

## Report

- **Done:** sidebar link History (`#history`, a pure `pageFromHash`); `History.tsx`: all attempts, a
  Download per row, "Download all logs (N)" (one JSON file: `format`, `version`, `exported`,
  `count`, `logs`); the Arena table has no Download column and lists the latest 10 with a link to
  History; shared columns in `components/attemptColumns.tsx`; attempts kept in `App`; paths now
  kept for the newest 100 attempts (was 30).
- **Tests:** `bun test` 65 passed, typecheck and build clean; Python untouched.
- **Left:** not clicked in a browser. Attempts older than the newest 100 show a dash. Restart nothing
  server-side: only the page changed (reload the page).
- **Lessons:** in LESSONS.md.
