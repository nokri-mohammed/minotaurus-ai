# G16: one start/stop button and a brain-loading animation

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** web
- **Model:** opus
- **CEO go:** 2026-11-24

## Goal

1. One button: `▶ Start run` when idle, `■ Stop` while a run goes (no greyed-out Stop).
2. A small brain animation, shown only while a brain file loads, on screen for at least about 0.7 s.

## How to build it (tests first)

1. `runButton.ts`: the label for each state.
2. `minimumTime.ts`: `atLeast(work, ms)` keeps a fast load on screen long enough, also when it fails.
3. `components/BrainLoader.tsx`: SVG network, CSS pulse, stops under reduce-motion; the text
   "Loading brain..." stays.
4. `Arena.tsx`: a `loadingBrain` state; no second load while one runs. No server or contract change.

## Report

- **Done:** one run button (`▶ Start run`, primary; `■ Stop` while running, secondary; Start is disabled
  until a brain is loaded and while one loads); `BrainLoader` built from the CEO's
  `brain-svgrepo-com.svg` (Twemoji): a grey brain with the coloured brain rising through a wavy mask,
  about 3 s per fill, shown only while a brain loads, held with `atLeast(..., 3000)`; the animation
  stops under reduce-motion (the brain shows full). Credit added to README.md (CC-BY 4.0).
- **Tests:** `bun test` 61 passed, typecheck and build clean; Python untouched. The fill was checked
  as screenshots of paused frames (t = 0.1, 0.8, 1.6, 2.6 s) in headless Chromium.
- **Left:** not clicked in a browser. The 3 s hold slows loading on purpose (`MIN_LOADING_MS`).
- **Lessons:** in LESSONS.md.
