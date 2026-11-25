# T1: training that does not loop

- **Owner:** minotaurus-ai-dev (the lead), working now (CEO go: 2026-11-25 "implement all from 1 to 5")
- **Area:** engine, trainer, brain loader, server, web (recipe rows)
- **Model:** sonnet
- **Asked by the CEO:** 2026-11-25 ("how to improve the training to make it not loop")
- **Training code:** it is Mo's code. The CEO's go covers this card. I do not start training.

## What (all five, every one off by default so old configs and brains behave as before)

1. **Memory in the input (obs_version 2).** `"observation": {"version": 2}`: the 77 numbers plus
   the last move (4 numbers, one-hot) and whether it bumped (1), and visit counts up to 8 (not 3).
   82 numbers in. The loader accepts versions 1 and 2 and checks the input size per version.
2. **Train against loops.** `"loop_stop": {"repeats": 3, "penalty": 0.5}`: a training try ends when
   the dot is in the same square seeing the same input for the third time, with a penalty.
3. **Choose on loops too.** The quiz (validation) counts mazes where the brain loops. Same score:
   fewer loops wins, for the saved try and for the best seed. The results table gets a Loops column.
4. **Teach from the shortest path.** `dqn.imitation`: for the first tries, a teacher (the shortest
   way to the exit) steers some moves, and a large-margin loss pulls the network towards the
   teacher's move. Then plain learning goes on.
5. **Break loops when playing.** `"loop_escape": true`: a brain that is in the same square seeing
   the same input for the third time plays one random free move (seeded, so runs repeat). Written
   into the `.onnx` as `loop_escape`.

## Done means

Tests for each part, ruff clean, full pytest, schema regenerated, README/TRAINING.md updated,
recipe rows on the page, report with lessons. The CEO runs the training.

## Report

- **Done:** all five, each off by default.
  1. `observation.version` 2: `observe()`, `MazeEnv`, `Race`, the loader (accepts 1 and 2, checks the
     input size per version, `Brain.obs_version`), `export_dqn`/`export_qtable` (82 inputs, five more
     key weights so the first 77 keep their key), `DQNAgent(obs_len=)`. Every place that plays a brain
     (arena, scoring, `play`) builds its env from `obs_version_of(brain)`.
  2. `loop_stop`: `LoopWatch` (`engine/loops.py`), used in the training loop; metrics line `loop_stops`.
  3. `validation_check` returns (score, loops); a tie on score keeps the brain with fewer loops;
     `pick_best` compares whole-percent scores, then loops; results table has a `loops` column.
     The metrics endpoint now copies only the quiz fields it draws (a new key would have dropped the
     whole quiz line).
  4. `dqn.imitation`: `Teacher` (BFS distance to the exit), a teacher share that falls to 0, and a
     large-margin loss in `DQNAgent.imitate`.
  5. `loop_escape`: `player()` plays one random free move on the third repeat of a state, following the
     square from its own moves (`DeadReckoning`); metadata `loop_escape`.
  Also: recipe rows and four help texts on the page, `data/examples/dqn-no-loops-brain.json`,
  TRAINING.md section "Against loops", schema regenerated.
- **Tests:** `uv run pytest`: 511 passed (24 new in `tests/test_loops.py`, 7 in `tests/test_memory_obs.py`);
  `ruff check` and `ruff format --check` clean; web `bun test` 88 pass, typecheck and build clean.
- **Not done:** no training was run, so none of the five is shown to help yet. Loop stop and imitation
  have only had tiny test runs. Bundles made before this card still load unchanged.
- **Lessons:** a loop is the same square and the same input, not the input alone (a corridor looks the
  same everywhere); a strict model fed `**row` drops the whole line when a new key appears.
