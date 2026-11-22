# How training works

A "brain" is a small program that walks a dot through a maze to the exit. You train one by letting
the dot play the maze many times and rewarding it. This page explains the two methods we have.
Both end in the same `.onnx` brain file, so both run in the arena the same way.

```sh
uv run minotaurus train --config data/examples/qtable-brain.json
uv run minotaurus train --config data/examples/dqn-brain.json
```

## What the brain sees and does

- **Input: the view.** At every step the dot sees a 5 x 5 square of cells around itself, not the
  whole maze. The game turns it into **77 numbers**:
  - 25 numbers for walls (`1` wall, `0` free),
  - 25 numbers for the exit (`1` exit, `0` not),
  - 25 numbers for visited (`1` been there, `0` not yet),
  - 2 numbers for the exit direction (each `-1`, `0` or `1`).
- **Output: 4 scores**, one for each move (up, down, left, right). The dot takes the highest.

Where the 77 comes from: 5 x 5 = 25 cells, times 3 layers = 75, plus 2 = 77
(`obs_size()` in `minotaurus/engine/observe.py`).

## Rewards

The game gives a reward after every move (`minotaurus/engine/env.py`). They are game rules, so they
are not in the config file.

| Event | Reward |
|---|---|
| Reach the exit | +1 |
| Every step | -0.01 |
| Hit a wall | -0.05 |

The step cost is what makes a short path score higher than a long one.

## The training loop

One **episode** is one trip from the start to the exit, or until the step limit. Training repeats
it for the number of `episodes` in the config. In each episode, for every step:

1. **See:** the game gives the dot its view.
2. **Choose:** usually the move with the highest score. Sometimes (`epsilon`) a random move, so the
   dot keeps exploring. Early on almost every move is random.
3. **Move:** the game applies it and returns a reward.
4. **Learn:** the method updates its scores from that reward (this is where the two methods differ).

Over many episodes the exit's +1 spreads backwards along the path, and `epsilon` shrinks, so the dot
explores less and uses what it learned more. The code is in `minotaurus/trainer/train.py`.

## Method 1: Q-table

A **lookup table** with one entry per view the dot has met. Each entry has 4 scores:

```
view                         up     down    left    right
view A  [0,1,0,0,1,...]      0.10   0.00    0.05    0.70
view B  [1,1,0,0,0,...]      0.00   0.30    0.00    0.00
```

The table starts empty. A new view gets a new entry with all scores at 0.

**Learning:** after a move, its score is updated to move towards
`reward + gamma × (best score in the next view)`. So a move is worth what it pays now plus what the
best move after it is worth. `learning_rate` is how fast scores change and `gamma` is how much
future reward counts.

**Good:** simple, fast, easy to read, reaches 100% on `easy-01` (395 entries, 13 steps, the shortest
path).
**Limits:** two different places can give the same view and share one entry. A bigger maze means
many more views, so the table grows and only suits small mazes. It cannot handle a view it has never
met.

Code: `minotaurus/trainer/qtable.py`. Settings: the `qtable` block of the config.

## Method 2: DQN (neural network)

Instead of a table, a small **neural network** (77 numbers in, hidden layers, 4 scores out) holds
adjustable numbers. It learns a pattern, so it can give sensible scores for views it has never met.

**Learning:** each step is stored in a **replay buffer**. On every step the network trains on a
random batch from the buffer, so it does not just learn from the last few moves. A second copy of
the network, the **target network**, is updated only every `target_update` steps, to keep training
stable. The update aims at the same idea as the Q-table: `reward + gamma × best next score`.

**Good:** handles views it has not seen, so it scales to bigger and new mazes.
**Limits:** slower, needs more settings, and training can be unstable.

Code: `minotaurus/trainer/dqn.py`. Settings: the `dqn` block of the config.

## Settings and output

- A config file sets the method, the levels, the number of episodes, the seed and the method's own
  block. Examples: `data/examples/`. The schema is `data/schemas/brain-config.schema.json`.
- The same seed gives the same training run.
- A run writes `runs/<name>/<time>/` with `metrics.jsonl` (reward, steps, success rate per
  window), `checkpoints/`, `config.json` and `brain.onnx`. `runs/` is not committed.
- Check a brain with `uv run minotaurus check-brain <file.onnx>` and watch it with
  `uv run minotaurus play --brain <file.onnx>`.

## Not built yet

See `BACKLOG.md`: a maze generator with train, validation and test sets, better metrics, random and
shortest-path opponents, and keeping the best brain instead of the last. Other methods (PPO,
behaviour cloning) are later ideas.
