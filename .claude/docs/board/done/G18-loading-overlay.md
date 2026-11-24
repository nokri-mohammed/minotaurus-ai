# G18: brain loader as a centred overlay

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** web
- **Model:** opus
- **CEO go:** 2026-11-24 ("load brain should be displayed in the center of the screen with overlay")

## Report

- **Done:** `components/LoadingOverlay.tsx`: a dimmed full-screen layer with a white card in the
  middle holding the filling brain (140 px) and "Loading brain..."; shown only while a brain loads
  (still held 3 s); `BrainLoader` takes a `size`; the small loader in the status line is gone
  (the text stays). It fades in over 0.2 s (no animation under reduce-motion) and the page behind
  it cannot be clicked.
- **Tests:** `bun test` 65 passed, typecheck and build clean. Checked as a screenshot of the real
  stylesheet in headless Chromium: the card is centred.
- **Left:** not tried with a real upload in a browser. "Download all logs" (G17) already saves one
  file with every log in it; the CEO asked about it in the same turn, nothing changed there.
- **Lessons:** in LESSONS.md.
