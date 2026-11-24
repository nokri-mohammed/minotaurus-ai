# G14: wide mixed-size example (9 to 21)

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** trainer (example config, docs)
- **Model:** opus
- **CEO go:** 2026-11-24 ("yes go")

## Goal

The R3 recipe on sizes 9, 11, 13, 17 and 21, to see whether the brain then finishes the larger
hand-made levels (hard-02 is 21x21).

## Report

- **Done:** `data/examples/dqn-mixed-wide-learning-brain.json`: the recipe of
  `dqn-mixed-learning-brain.json` unchanged, 750 / 150 / 150 mazes (150 / 30 / 30 per size),
  `seeds` [1, 2, 3, 4], `parallel` 4. A test checks the recipe is the same and the piles hold all five sizes.
  TRAINING.md records the real result of the 9 to 13 run (20 min, validation 93 to 95%, best seed 5 of 7 hand-made levels).
- **Not run by me:** the CEO runs it. Time is a guess (bigger mazes mean longer tries): an hour or more.
- **Left:** the run; impossible-01 (41x41) is a stretch and not promised.
- **Lessons:** change one thing between runs: this config differs from the last only in the mazes.
