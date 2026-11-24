# G23: server keeps several brains and attempts (SQLite)

- **Owner:** minotaurus-ai-dev (the lead)
- **Area:** server, contract
- **Model:** opus
- **CEO go:** 2026-11-24 ("yes do all of them, do not push until I test them locally")

## Report

- **Done:**
  - `minotaurus/server/store.py`: SQLite (standard library) in `var/arena.db` (git-ignored), memory
    in tests. Tables `brains` (id, name, method, added_at, kind, the uploaded file as a blob; cap
    50) and `attempts` (cap 5000). The brain file lives in the database, not in `var/brains/`:
    one file to back up, nothing to name safely.
  - `POST /api/brain` takes a `.onnx` or a bundle `.tar` (detected by the tar header). The reply has
    the id (sha256 of brain.onnx), name, method, `has_recipe`, `added_at`. A bundle is checked by
    `read_bundle`; a refused upload changes nothing. The same brain twice is one row; a plain
    file never replaces a bundle.
  - `GET /api/brains`, `GET /api/brains/{id}/recipe` and `/graph.png` (bundles only, else 404),
    `GET/POST /api/attempts`, `POST /api/attempts/import` (safe to repeat).
  - `/ws/run?level_id=&brain_id=`: a run names its brain; without `brain_id` it uses the last
    loaded one (as before). After a restart the brain is rebuilt from the database.
  - `minotaurus serve` uses `make_app` (database in `var/`); `create_app()` stays in memory.
  - Contract: Pydantic models, `messages.schema.json`, samples (zod comes with the page, G24).
- **Tests:** full suite passed (see the commit), ruff clean.
- **Left:** the page (G24), run all levels (G25), the Brains page (G26).
- **Lessons:** a blob in SQLite is simpler than files by hash for brains this small.
