# G4: best brain on validation

- **Owner:** Mo (rackiavic), with Claude Code
- **Area:** trainer
- **Backlog:** G4 in `BACKLOG.md` (cut from it, 2026-11-23). Agreed by the repo owner as the
  default with generated pools, not an opt-in.

## Goal

Export the best brain on the validation mazes, not the last one (the last can be worse). Log which
episode was exported.

## How to build it (tests first)

1. Config `eval_every` (generated levels only). Unset means 250 with pools; 0 switches it off.
2. Every `eval_every` tries and at the last try, play the brain on the validation mazes without
   random moves; keep a copy of the best one. A tie keeps the later brain.
3. Export that copy. If every check scored 0%, export the final brain and log a warning.
4. Log each check and the chosen episode in `metrics.jsonl`; put the chosen episode in the `.onnx`
   metadata (`exported_episode`); `minotaurus train` prints it.

## Report

- **Done:** all four steps. `scores.json` keeps its three keys; `training.png` skips the
  validation lines.
- **Tests:** a worse last brain is not exported (the exported brain gives the episode 4 brain's
  scores); a tie exports the later brain; all 0% exports the final brain with a warning; the last
  try is always checked; `eval_every: 0` exports the last brain with no checks; the check plays
  without random moves; the CLI prints the episode.
- **The one changed default:** configs with generated levels now export the best brain on
  validation. `qtable-generated.json` exported the final brain (episode 6000) before; see the PR
  for the episode it exports now.
- **Research:** in the 2026-11-23 DQN runs, two brains that collapsed in their last 500 tries
  scored 0% on test as the last brain and 62% and 64% as the best checkpoint on validation.
- **Lessons:** see LESSONS.md (2026-11-23, best brain on validation).
