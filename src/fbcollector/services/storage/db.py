"""SQLite connection lifecycle and schema management for the temporary session cache."""

import sqlite3
import threading
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    username TEXT NOT NULL,
    comment TEXT NOT NULL,
    employee_id TEXT,
    detected_time TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_raw_comments_detected_time ON raw_comments(detected_time);

CREATE TABLE IF NOT EXISTS unique_users (
    username TEXT PRIMARY KEY,
    first_comment_time TEXT NOT NULL,
    comment_count INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS employee_ids (
    employee_id TEXT PRIMARY KEY,
    first_user TEXT NOT NULL,
    first_time TEXT NOT NULL,
    duplicate_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS winner_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    winner_name TEXT NOT NULL,
    employee_id TEXT,
    prize TEXT,
    drawn_at TEXT NOT NULL
);
"""

_TABLES = ("raw_comments", "unique_users", "employee_ids", "winner_history")


class SQLiteConnectionManager:
    """Owns a single SQLite connection used by the Writer thread and UI-triggered reads.

    SQLite connections are not safe to share across threads by default, so this manager
    opens the connection with ``check_same_thread=False`` and serializes access with a
    lock; the app's design only ever has one writer (``WriterThread``), with occasional
    read-only queries from the UI thread (search/pagination), which SQLite's WAL mode
    handles well for concurrent readers.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._connection is None:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(str(self._db_path), check_same_thread=False)
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA synchronous=NORMAL")
            self._connection.row_factory = sqlite3.Row
            self.initialize_schema()
        return self._connection

    def initialize_schema(self) -> None:
        connection = self._connection or self.connect()
        with self._lock:
            connection.executescript(_SCHEMA)
            connection.commit()

    def reset(self) -> None:
        """Drop and recreate all tables. Used by Clear Session."""
        connection = self.connect()
        with self._lock:
            for table in _TABLES:
                connection.execute(f"DELETE FROM {table}")
            connection.commit()

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @property
    def lock(self) -> threading.Lock:
        return self._lock
