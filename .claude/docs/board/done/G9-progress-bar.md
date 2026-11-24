# G9: progress bar while training

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** trainer, cli
- **Model:** opus
- **Rule from the CEO:** extend Mo's work, do not refactor it; no new dependency.

## Goal

While `train` runs, the terminal shows how far it is: a bar, the percent, the try count and the
time left.

## How to build it (tests first)

1. `minotaurus/trainer/progress.py`: pure helpers (`bar`, `percent`, `time_left`, `single_line`,
   `multi_line`).
2. One run: the CLI redraws one line in place on a terminal; on a pipe or file it prints the old
   lines (nothing changes for logs).
3. Several seeds: each worker reports its try count through a queue; `run_seeds` takes an optional
   `on_progress(seed, episode)`; the CLI shows one overall bar.
4. `metrics.jsonl` stays as it is.

## Report

- **Done:** `trainer/progress.py` (`bar`, `percent`, `time_left`, `single_line`, `multi_line`); one run
  redraws one line on a terminal, plain lines on a pipe; `run_seeds(on_progress=...)` with a queue
  from each worker; one overall bar for several seeds. No new dependency, `metrics.jsonl` unchanged.
- **Tests:** `uv run pytest` 341 passed, ruff clean. Real run on a fake terminal (`script`): single
  run showed `[░░░░] 0% try 10/3000 ... left 8.9 s`; two seeds showed `[█░░░] 5% seeds done 0/2
  left 51.9 s`, then the "seed N done" lines.
- **Left:** the time left is high in the first windows (start-up cost); no per-seed bars; the web
  page has no training view.
- **Lessons:** in LESSONS.md.
