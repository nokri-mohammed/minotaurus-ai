"""The arena's small database (SQLite, Python's standard library): loaded brains and attempts.

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
MAX_ATTEMPTS = 5000  # the oldest attempts are dropped over this

SCHEMA = """
CREATE TABLE IF NOT EXISTS brains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    method TEXT NOT NULL,
    added_at TEXT NOT NULL,
    kind TEXT NOT NULL,
    data BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    brain_id TEXT NOT NULL,
    brain TEXT NOT NULL,
    method TEXT NOT NULL,
    level TEXT NOT NULL,
    result TEXT NOT NULL,
    steps INTEGER NOT NULL,
    seconds REAL NOT NULL,
    path TEXT
);
CREATE INDEX IF NOT EXISTS attempts_by_brain ON attempts (brain_id, date);
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

    # ---- attempts ----

    def add_attempt(self, attempt: dict) -> None:
        """Save one attempt. An id that is already saved is left as it is."""
        path = attempt.get("path")
        path_text = None
        if path is not None:
            path_text = json.dumps(path, separators=(",", ":"))
        with self._lock:
            self._db.execute(
                "INSERT OR IGNORE INTO attempts "
                "(id, date, brain_id, brain, method, level, result, steps, seconds, path) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    attempt["id"],
                    attempt["date"],
                    attempt["brain_id"],
                    attempt["brain"],
                    attempt["method"],
                    attempt["level"],
                    attempt["result"],
                    attempt["steps"],
                    attempt["seconds"],
                    path_text,
                ),
            )
            self._drop_old_attempts()
            self._db.commit()

    def _drop_old_attempts(self) -> None:
        self._db.execute(
            "DELETE FROM attempts WHERE id IN "
            "(SELECT id FROM attempts ORDER BY date DESC, rowid DESC LIMIT -1 OFFSET ?)",
            (MAX_ATTEMPTS,),
        )

    def list_attempts(self, brain_id: str | None) -> list[dict]:
        """Newest first; one brain, or all of them when brain_id is None."""
        query = "SELECT * FROM attempts"
        arguments: tuple = ()
        if brain_id is not None:
            query += " WHERE brain_id = ?"
            arguments = (brain_id,)
        query += " ORDER BY date DESC, rowid DESC"
        with self._lock:
            rows = self._db.execute(query, arguments).fetchall()
        attempts = []
        for row in rows:
            item = dict(row)
            path_text = item.pop("path")
            if path_text is not None:
                item["path"] = json.loads(path_text)
            attempts.append(item)
        return attempts
