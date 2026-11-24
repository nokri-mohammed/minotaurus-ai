# G26: the Brains page

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** web
- **Model:** opus
- **CEO go:** 2026-11-24 ("yes do all of them, do not push until I test them locally")

## Report

- **Done:** a Brains page (`#brains`, in the menu): a table with a row per brain (exam, quiz,
  portal levels, latest run-all, exam mazes, network, learning rate); an "Exam score over time"
  chart for one exam pile (a Select appears when several piles exist); "Compare two brains" showing
  only the settings that differ and the results side by side, with a warning when the exam mazes
  differ. Logic is pure and tested (`brainsView.ts`).
- **Tests:** `bun test` 80 passed, typecheck and build clean.
- **Not seen:** the page in a browser.
- **Left:** compare uses one seed per brain; a "recipe" view that takes the median of its seeds is
  not built. Plain `.onnx` brains have no settings to compare.
