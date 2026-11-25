"""The arena's small database (SQLite, Python's standard library): loaded brains and "run all levels" batches.

One file (var/arena.db), or memory when no path is given (tests). A brain is stored as the file
that was uploaded (a bundle .tar or a plain .onnx), so the list survives a server restart.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

MAX_BRAINS = 50  # the oldest brains are dropped over this
MAX_BATCHES = 500  # the oldest "run all levels" results are dropped over this

SCHEMA = """
CREATE TABLE IF NOT EXISTS brains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    method TEXT NOT NULL,
    added_at TEXT NOT NULL,
    kind TEXT NOT NULL,
    data BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS batches (
    id TEXT PRIMARY KEY,
    brain_id TEXT NOT NULL,
    date TEXT NOT NULL,
    total INTEGER NOT NULL,
    finished INTEGER NOT NULL,
    results TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS batches_by_brain ON batches (brain_id, date);
"""


class Store:
    def __init__(self, path: str | Path | None = None) -> None:
        if path is None:
            target = ":memory:"
        else:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            target = str(path)
        # One connection shared by the server's worker threads, one call at a time.
        self._lock = threading.Lock()
        self._db = sqlite3.connect(target, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(SCHEMA)

    # ---- brains ----

    def add_brain(self, brain_id: str, name: str, method: str, kind: str, data: bytes) -> None:
        """Save a brain. The same id again keeps one row; a bundle is never replaced by a plain
        file (the bundle carries the recipe)."""
        added_at = datetime.now(UTC).isoformat(timespec="seconds")
        with self._lock:
            row = self._db.execute("SELECT kind FROM brains WHERE id = ?", (brain_id,)).fetchone()
            if row is not None:
                if row["kind"] == "bundle" and kind == "onnx":
                    return
                self._db.execute("DELETE FROM brains WHERE id = ?", (brain_id,))
            self._db.execute(
                "INSERT INTO brains (id, name, method, added_at, kind, data) VALUES (?, ?, ?, ?, ?, ?)",
                (brain_id, name, method, added_at, kind, data),
            )
            self._drop_old_brains()
            self._db.commit()

    def _drop_old_brains(self) -> None:
        rows = self._db.execute("SELECT id FROM brains ORDER BY rowid DESC").fetchall()
        for row in rows[MAX_BRAINS:]:
            self._db.execute("DELETE FROM brains WHERE id = ?", (row["id"],))

    def list_brains(self) -> list[dict]:
        """Newest first: id, name, method, added_at, kind (without the file)."""
        with self._lock:
            rows = self._db.execute(
                "SELECT id, name, method, added_at, kind FROM brains ORDER BY rowid DESC"
            ).fetchall()
        brains = []
        for row in rows:
            brains.append(dict(row))
        return brains

    def get_brain_data(self, brain_id: str) -> tuple[str, bytes] | None:
        """(kind, file bytes) of a brain, or None."""
        with self._lock:
            row = self._db.execute(
                "SELECT kind, data FROM brains WHERE id = ?", (brain_id,)
            ).fetchone()
        if row is None:
            return None
        return row["kind"], bytes(row["data"])

    # ---- "run all levels" batches ----

    def add_batch(self, batch: dict) -> None:
        """Save one batch: id, brain_id, date, total, finished and the list of per-level results.

        A brain keeps only its latest batch: the same brain plays the same levels with the same
        seeds, so an earlier batch would only repeat it.
        """
        with self._lock:
            self._db.execute("DELETE FROM batches WHERE brain_id = ?", (batch["brain_id"],))
            self._db.execute(
                "INSERT OR IGNORE INTO batches (id, brain_id, date, total, finished, results) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    batch["id"],
                    batch["brain_id"],
                    batch["date"],
                    batch["total"],
                    batch["finished"],
                    json.dumps(batch["results"], separators=(",", ":")),
                ),
            )
            self._db.execute(
                "DELETE FROM batches WHERE id IN "
                "(SELECT id FROM batches ORDER BY date DESC, rowid DESC LIMIT -1 OFFSET ?)",
                (MAX_BATCHES,),
            )
            self._db.commit()

    def list_batches(self, brain_id: str) -> list[dict]:
        """The batches of one brain, newest first."""
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM batches WHERE brain_id = ? ORDER BY date DESC, rowid DESC",
                (brain_id,),
            ).fetchall()
        batches = []
        for row in rows:
            item = dict(row)
            item["results"] = json.loads(item["results"])
            batches.append(item)
        return batches
