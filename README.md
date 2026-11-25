<p align="center">
  <img src="web/public/icon.jpeg" alt="minotaurus-ai logo" width="200" />
</p>

# minotaurus-ai

Train a "brain" that solves a 2D maze with reinforcement learning (a Q-table or a neural network),
export it as an `.onnx` file, then run it in the arena and see how it scores. Later: race a
friend's brain online.

**Status:** the engine, trainer, local arena server and arena page are built (MVP). Design: `.claude/docs/plans/minotaurus-ai.md`.

## Layout

```
minotaurus/            Python package
  cli/                 the `minotaurus` command: one file per command
  engine/              the only copy of the game rules (levels, observe, MazeEnv, Race)
  trainer/             Q-table and DQN training, metrics, checkpoints, ONNX export
  brain/               safe loading of untrusted .onnx brains
  server/              FastAPI game server: rooms, uploads, race loop, WebSocket
data/
  schemas/             JSON Schemas: level, brain config, messages
  levels/              maze levels (JSON, easy to impossible); test-mazes/ = saved test mazes for the portal
  examples/            example brain configs (added in stage 2)
tests/                 pytest
web/                   TypeScript page (Bun, Vite): lobby, race, result; draws only
runs/                  training output (not committed)
```

## Run the skeleton

```sh
uv sync
uv run minotaurus hello          # CLI
uv run pytest                    # tests
uv run minotaurus serve          # server on http://127.0.0.1:8000/api/hello

cd web && bun install            # once
uv run minotaurus dev            # server and page together; open http://127.0.0.1:5173
uv run minotaurus dev --mock     # page with a fake arena inside Vite (to be removed, the real server exists)
```

## How training works

[TRAINING.md](TRAINING.md) explains the rewards, the training loop and the two methods (Q-table and DQN). Against loops, see "Against loops" there: `data/examples/dqn-no-loops-brain.json` turns all five anti-loop options on.

## Brains, bundles and the arena database

Training writes `bundle.tar` next to each `brain.onnx` (several seeds also write `best-bundle.tar`).
When you have a signing key the names say so: `bundle.signed.tar` and `best-bundle.signed.tar`:
the brain plus its manifest, settings (`config.json`), scores, graph and metrics. Load the `.tar` in
the Arena and the page shows how the brain was made (Recipe panel), scores it on every level, and
the Brains page compares brains and shows the exam trend. A plain `.onnx` still loads, without a
recipe. For a run made before bundles existed: `uv run minotaurus pack runs/<name>/<time>/seed-N`.

The server keeps loaded brains and their "run all levels" results in `var/arena.db` (SQLite, git-ignored), so they
survive a restart. The brain id is the sha256 of its `brain.onnx`; the page shows the first 8
characters. "Run all levels" plays the 19 portal levels at full speed and saves the result.

**Random maze page.** Its own page in the sidebar (`#random`). Pick the brain, a difficulty (easy 5 to
9, medium 11 to 17, hard 19 to 41) and a size, optionally tick "Exit in the outer wall" or "Random
start" and type a seed, then press **Generate**. The maze is drawn on the LED screen and runs with the
Start button. Its name carries the seed (the same seed and size give the same maze). It is only for
watching: never scored or saved. **Run all levels** in the Arena stays the fixed 19 levels.

**Brains page.** One table of every loaded brain with the same scores: **Stars** (the share of levels
it finished in "run all levels", as in the Arena rating), exam, quiz, portal levels and more. Click a
row to open `#brains/<id>`, the brain's own page: rating, the result on every level with **Run all
levels**, the training settings and graphs, the Signed and Verified badges, and a **Download** button.
The Arena also has a Download button for the selected brain. It saves the file that was loaded (the
`.tar` bundle, or the plain `.onnx`).

**Compare page.** Pick two brains to see only the settings that differ and their results side by
side (a warning shows when their exam mazes differ).

**Signing and checking.** Run `uv run minotaurus keygen` **once per computer**. It writes your signing
key to `~/.config/minotaurus/signing.key` (or the file in `$MINOTAURUS_SIGNING_KEY`). After that,
`train` and `pack` sign every bundle by themselves; there is nothing more to run. Before training
starts, `train` prints `Signing: on` (with your author id) or `Signing: off` (with how to fix it). `uv run minotaurus
sign <bundle.tar>` signs an old bundle and writes it next to the original as `<name>.signed.tar`.

- The same key gives the same author id on every bundle, so the id means "made by you".
- `keygen` never overwrites a key (a new key would be a new author id): a second run stops with
  "already exists".
- Back the key file up and keep it private. If you lose it the id is gone; old bundles keep the old
  id. On a second computer, copy the file to keep the id, or run `keygen` there for a separate one.
- Without a key everything still works and bundles are **Unsigned**. Signing only matters when you
  share a brain with someone else (the online race).

The Recipe panel shows **Signed** with your author id (a short fingerprint of the key) or
**Unsigned**. A signature proves who made the bundle and that it is unchanged; it does not prove the
scores. For that the server plays the brain again on its exam mazes and shows **Verified** when the
scores match what the bundle claims.

## Work board

`BACKLOG.md` lists what is not started, with how to build it; `minotaurus/BOARD.md` and
`web/BOARD.md` are the kanbans. Cards: `.claude/docs/board/`, one Markdown file per task in `todo/`,
`doing/`, `done/` or `blocked/`.

## Credits

The brain drawing shown while a brain loads (`web/src/components/BrainLoader.tsx`) is the Twemoji
"brain" by Twitter, Inc. and other contributors, licensed CC-BY 4.0 (https://github.com/twitter/twemoji),
taken from SVG Repo.
