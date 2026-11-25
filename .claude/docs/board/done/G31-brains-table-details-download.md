# G31: Brains table, details sheet, download

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** server, web
- **Model:** sonnet
- **CEO go:** 2026-11-25 (asked in the session)

## Report

- **Done:** `GET /api/brains/{id}/download` returns the file that was loaded (`.tar` or `.onnx`) as an
  attachment, 404 for an unknown id. The Brains table has Method and Added columns, and each row is a
  button (click or Enter) that opens the brain's own page `#brains/<id>` (rating, run all levels with
  per-level results, Recipe with training graphs, Signed and Verified, Download). The table has a Stars
  column. The list page no longer has the levels select or Run all levels (CEO correction). The Arena has a Download button for the selected brain.
- **Tests:** pytest download tests (bundle and plain onnx, 404), `bun test` 82 passed, typecheck and
  build clean. Not seen in a browser.
- **Left:** `dev --mock` has no download endpoint; sorting or filtering the table is not built.
- **Lessons:** a plain link with `download` needs no fetch code, so the service layer only builds the URL.
