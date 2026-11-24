# G22: the brain bundle (.tar)

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** trainer, cli, server (reading side comes in G23)
- **Model:** opus
- **CEO go:** 2026-11-24 ("yes do all of them, do not push until I test them locally")

## Report

- **Done:** `minotaurus/bundle.py`: Pydantic `Manifest` (format, version 1, brain_id = sha256 of
  brain.onnx, name, method, every file with size and sha256), `build_bundle(run_dir)`,
  `read_bundle(bytes)`. Training (single run and each seed) writes `bundle.tar` after the graph;
  several seeds also copy `best-bundle.tar`. `uv run minotaurus pack <run folder>` packs older runs.
  Schema: `data/schemas/bundle-manifest.schema.json` (generated, a test checks it).
- **Refused with a message:** not a tar, too big, too many members, links or folders, names outside
  the allow-list, a missing or changed file, extra files, unknown version, bad brain (the same load
  checks as a plain upload), invalid config.json, names that differ, brain_id not the hash.
- **Tests:** 379 passed, ruff clean. Packed the real wide-run seed 4 (350 KB).
- **Left:** the server reads bundles (G23); the check "pools in the brain match the config" is not
  done (only the three names are compared).
- **Lessons:** the plot is drawn after train() returns, so the bundle is built after the plot.
