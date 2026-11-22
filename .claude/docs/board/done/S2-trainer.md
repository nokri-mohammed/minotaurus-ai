# S2: trainer, both methods, ONNX export, check-brain

- **Owner:** minotaurus-ai-dev
- **Area:** trainer
- **Model:** sonnet
- **Design:** ../../plans/minotaurus-ai.md, section Technical Plan (Trainer)

## Goal
`minotaurus train --config <file>.json` trains a brain with a Q-table or a DQN and writes
`brain.onnx`. `check-brain` validates a file. `play --brain <file>` shows a brain solving `easy-01`.

## Scope (do / do not)
Do: config check, examples, Q-table, DQN (torch CPU), training loop with metrics and checkpoints,
export (ONNX equals in-memory brain), safe brain loader (`minotaurus/brain/onnx_brain.py`),
CLI `train`, `check-brain`, `play --brain`. New dependencies approved by the CEO: torch (CPU),
onnx, onnxruntime. Do not: touch `web/`, start S3, commit `runs/` or `.onnx` files.

## Done when
Both example configs train on easy-01 and `play --brain` shows each solving it; the loader rejects
oversize, wrong shape, forbidden operator, wrong obs_version and slow models; pytest and ruff pass.

## Original backlog write-up

**Goal.** `minotaurus train --config <file>.json` trains a brain with a Q-table or a DQN and writes
`brain.onnx`. `check-brain` validates a file. `play --brain <file>` shows a brain solving `easy-01`.

**How to build it (tests first for each step):**

1. **Config check** (`minotaurus/trainer/config.py`): load JSON, validate against
   `data/schemas/brain-config.schema.json` (already written), and turn the first error into a
   message naming the setting. Resolve `levels` ids with `load_level_by_id`.
2. **Examples** (`data/examples/qtable-brain.json`, `dqn-brain.json`): small, ready to run on
   `easy-01`. Tests validate both against the schema.
3. **Q-table** (`trainer/qtable.py`): table is a dict keyed on the whole observation (the 77 numbers
   turned into one integer: exit direction as 2 x 2 bits plus the 75 window bits). Update rule
   `Q[s,a] += lr * (r + gamma * max Q[s'] - Q[s,a])`, epsilon-greedy with the decay from config,
   unseen keys start at zeros. Test: on a 1 x N corridor it learns to go right in a few episodes.
4. **DQN** (`trainer/dqn.py`, needs `torch`, CPU build): MLP 77 -> hidden layers from config -> 4,
   replay buffer, target network copied every `target_update` steps, Adam, Huber loss, epsilon
   schedule. Test: loss drops on a fixed batch; one training step changes the weights.
5. **Training loop** (`trainer/train.py`): per episode run `MazeEnv`, call the method, every N
   episodes append one line to `runs/<name>/<date-time>/metrics.jsonl` (average reward, steps,
   success rate, epsilon, loss), write `checkpoints/`, copy the config, export at the end. Seeded:
   same seed gives the same metrics (test).
6. **Export** (`trainer/export.py`): DQN with `torch.onnx.export`; Q-table built with
   `onnx.helper`: 77 floats -> multiply by powers of two and sum to one integer key ->
   `LabelEncoder` (domain `ai.onnx.ml`) maps key to row index (unknown key -> a row of zeros) ->
   `Gather` the Q-row. Both carry metadata: name, method, `obs_version`, `window`, `memory`, level
   ids. **Test: the ONNX output equals the in-memory brain on the same observations.**
7. **Brain loader** (`minotaurus/brain/onnx_brain.py`): safe load with size limit (1 MB),
   `onnx.checker`, operator allowlist, input `[1,77]` and output 4 checks, `obs_version` check,
   per-step time limit with `onnxruntime`; returns a plain function `obs -> action`. Tests reject
   a big file, wrong shape, forbidden operator, wrong version, slow model. S3 reuses it.
8. **CLI:** `check-brain <file>` prints OK or the reason; `play --brain <file> --level <id>`.

**New dependencies (CEO go needed):** `torch` (CPU), `onnx`, `onnxruntime`.

**You can check:** train both examples; `play --brain` shows each solving `easy-01`.

**Risks.** Q-table size explodes on big mazes (fine for `easy-01`). DQN may need tuning of
epsilon decay to solve in minutes on CPU.

## Report

### What I did
- Added `torch` (CPU wheel via an explicit `pytorch-cpu` uv index in `pyproject.toml`), `onnx`,
  `onnxruntime` (CEO approved).
- `minotaurus/trainer/`: `config.py` (schema check, error names the setting, level ids or
  difficulty), `qtable.py`, `dqn.py`, `train.py` (metrics.jsonl, checkpoints every 500 episodes,
  config copy, seeded), `export.py` (both methods to ONNX with metadata).
- `minotaurus/brain/onnx_brain.py`: safe loader (1 MB, onnx checker, operator and domain allowlist,
  no external data, input `[1,77]`, output 4, `obs_version`, 50 ms per-step limit on a test run and
  on every call). Returns a `Brain` that is callable `obs -> action`.
- CLI: `train --config`, `check-brain <file>`, `play --brain <file> --level <id>`.
- Examples `data/examples/qtable-brain.json` and `dqn-brain.json`.
- 34 new tests (`tests/test_trainer.py`, one in `tests/test_cli.py`), written before the code
  was run; the key ones compare ONNX output with the in-memory brain for both methods.

### Real output
Training (outputs in `runs/`, not committed):
- Q-table, 3000 episodes: 100% success from episode ~900, 4 s on CPU.
- DQN, 600 episodes ([64, 64], 20k replay): 100% success from episode ~250, 23 s on CPU.
- `check-brain`: `OK: qtable-easy (qtable)` and `OK: dqn-easy (dqn)`.
- `play --brain <file> --level easy-01 --delay 0`: both end with `step 13/52` and
  `reached the exit` (the shortest path length).

```
$ uv run pytest
======================== 77 passed, 7 warnings in 3.79s ========================
$ uv run ruff check
All checks passed!
```
The 7 warnings are torch's deprecation notice for the legacy ONNX exporter (see lessons).

### What is left
- S3 (local arena server) reuses `load_brain`; not started.
- Q-table keys are a hash of the observation; fine for easy-01, table grows on large mazes.
- DQN export uses the legacy TorchScript exporter (`dynamo=False`) because the new one needs
  extra dependencies (onnxscript). Revisit if torch removes the legacy path.
- No resume from checkpoints yet (checkpoints are written, nothing reads them).

### Lessons
- 77 inputs do not fit one 64-bit integer as plain bits (79 bits needed), so the Q-table key is a
  hash: `sum((obs + 1) * weight)` with fixed random weights, same code in Python and in the ONNX
  graph. The write-up's "powers of two" idea was not possible.
- onnxruntime's int64 `ReduceSum` is only exact up to 2**53 (it lost low bits above that), while
  numpy is exact. Keep weights below 2**45 so the sum stays under 2**53. Found by a failing
  equality test, which is why that test exists.
- `uv add torch` with the CPU index fails when the index also hosts an older numpy; configure
  the index as `explicit = true` under `[tool.uv.index]` with `[tool.uv.sources]` for torch only.
