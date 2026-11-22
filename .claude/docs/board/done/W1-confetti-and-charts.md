# W1: confetti on a finish, progress charts on the page

- **Owner:** minotaurus-ai-dev
- **Area:** web
- **Model:** opus (done by the lead, no sub-agent)
- **Design:** ../../plans/minotaurus-ai.md, stage 4; CEO request 2026-11-22

## Goal

1. **Confetti** when a run reaches the exit (status `finished`), once, short, no click needed.
   Off when the player prefers reduced motion.
2. **Charts** on the arena page from the attempts saved in the browser: steps per finished attempt
   (are you improving?) and how many runs finished, timed out or failed.

## Scope

- Do: pure modules `web/src/confetti.ts` and `web/src/chart.ts` with `bun test` tests first;
  components `Confetti` and `AttemptsCharts` in `web/src/components/`; wire them in `Arena.tsx`;
  styles in `style.css`. Plain code, no new dependencies (canvas and SVG by hand).
- Do not: change the server or the message contract; delete files.
- Not possible here: a training graph. The `.onnx` file carries no training metrics, so the page
  cannot draw it. `train` already writes `training.png` per run.

## Done when

`bun test`, `bun run typecheck` and `bun run build` pass; in the page a finished run shows confetti
and the charts appear after attempts exist.

## Report

### What I did

- `web/src/confetti.ts`: `makePieces` and `stepPieces`, pure functions (gravity, sideways drift,
  spin, pieces below the screen are dropped). `components/Confetti.tsx` draws them on a fixed,
  click-through canvas: one burst of 140 pieces, at most 4 seconds, skipped when the player prefers
  reduced motion. `Arena.tsx` raises a counter when a run finishes, once per run.
- `web/src/chart.ts`: `stepsOverTime`, `countOutcomes`, `layoutLine` (the scale starts at zero, so a
  small change is not exaggerated). `components/AttemptsCharts.tsx` draws two charts in a new
  "Progress" panel: steps per finished run as an SVG line, and how runs ended as three bars with
  labels and counts (colour is never the only clue).
- Tests first: 10 new bun tests (`confetti.test.ts`, `chart.test.ts`), red before the code.
- No new dependencies: the canvas and the SVG are drawn by hand.

### What I verified (real output)

- `bun test`: 33 pass, 0 fail. `bun run typecheck` and `bun run build`: clean.
- I rendered the charts with sample attempts and took a screenshot with headless Chrome: the line
  falls from 38 to 13 steps and the bars show 5 finished, 1 timed out, 1 failed.

### What is left

- **Not seen by me:** the confetti animation (I cannot click through a run here) and the page with
  the real server. Check with `uv run minotaurus dev`, load a brain, press Start run.
- A training graph on the page is not possible: the `.onnx` file holds no training metrics.
  `train` writes `training.png` in the run folder. If you want it on the page, the server could read
  a `metrics.jsonl` next to the brain, which is a new card.

### Lessons

- Pure functions for the animation and chart maths (`stepPieces`, `layoutLine`) made them testable
  without a browser; only the thin canvas and SVG parts need eyes.
- A static render of a component with sample data plus a headless screenshot is a cheap way to see
  a chart when the inspector cannot click.

