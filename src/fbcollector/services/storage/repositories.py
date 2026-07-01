"""Repository pattern: all SQL lives here, callers work with dataclasses only."""

from datetime import datetime

from fbcollector.services.storage.db import SQLiteConnectionManager
from fbcollector.services.storage.models import EmployeeIdEntry, RawComment, UniqueUser, Winner


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


class CommentRepository:
    """Persists every raw comment (no de-duplication beyond the hash uniqueness)."""

    def __init__(self, db: SQLiteConnectionManager) -> None:
        self._db = db

    def insert_batch(self, comments: list[RawComment]) -> int:
        """Insert a batch in a single transaction. Duplicate hashes are silently ignored."""
        if not comments:
            return 0
        connection = self._db.connect()
        with self._db.lock:
            cursor = connection.executemany(
                """
                INSERT OR IGNORE INTO raw_comments
                    (hash, timestamp, username, comment, employee_id, detected_time)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        c.hash,
                        c.timestamp.isoformat(),
                        c.username,
                        c.comment,
                        c.employee_id,
                        c.detected_time.isoformat(),
                    )
                    for c in comments
                ],
            )
            connection.commit()
            return cursor.rowcount

    def count(self) -> int:
        connection = self._db.connect()
        row = connection.execute("SELECT COUNT(*) AS n FROM raw_comments").fetchone()
        return int(row["n"])

    def fetch_page(self, offset: int, limit: int) -> list[RawComment]:
        """Newest-first page, used by the virtualized live feed for scroll-back."""
        connection = self._db.connect()
        rows = connection.execute(
            """
            SELECT hash, username, comment, timestamp, employee_id, detected_time
            FROM raw_comments
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def search(self, query: str, limit: int = 500) -> list[RawComment]:
        """Case-insensitive substring search across username, comment, and employee id."""
        connection = self._db.connect()
        like = f"%{query}%"
        rows = connection.execute(
            """
            SELECT hash, username, comment, timestamp, employee_id, detected_time
            FROM raw_comments
            WHERE username LIKE ? OR comment LIKE ? OR employee_id LIKE ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (like, like, like, limit),
        ).fetchall()
        return [self._row_to_model(row) for row in rows]

    @staticmethod
    def _row_to_model(row) -> RawComment:
        return RawComment(
            hash=row["hash"],
            username=row["username"],
            comment=row["comment"],
            timestamp=_parse_dt(row["timestamp"]),
            detected_time=_parse_dt(row["detected_time"]),
            employee_id=row["employee_id"],
        )


class UserRepository:
    """Keeps only the first occurrence of each username; increments a running comment count."""

    def __init__(self, db: SQLiteConnectionManager) -> None:
        self._db = db

    def upsert_on_comment(self, username: str, comment_time: datetime) -> None:
        connection = self._db.connect()
        with self._db.lock:
            connection.execute(
                """
                INSERT INTO unique_users (username, first_comment_time, comment_count)
                VALUES (?, ?, 1)
                ON CONFLICT(username) DO UPDATE SET comment_count = comment_count + 1
                """,
                (username, comment_time.isoformat()),
            )
            connection.commit()

    def all(self) -> list[UniqueUser]:
        connection = self._db.connect()
        rows = connection.execute(
            "SELECT username, first_comment_time, comment_count FROM unique_users ORDER BY first_comment_time"
        ).fetchall()
        return [
            UniqueUser(
                username=row["username"],
                first_comment_time=_parse_dt(row["first_comment_time"]),
                comment_count=row["comment_count"],
            )
            for row in rows
        ]

    def count(self) -> int:
        connection = self._db.connect()
        row = connection.execute("SELECT COUNT(*) AS n FROM unique_users").fetchone()
        return int(row["n"])


class EmployeeRepository:
    """Keeps only the first occurrence of each employee ID; tracks duplicate sightings."""

    def __init__(self, db: SQLiteConnectionManager) -> None:
        self._db = db

    def upsert_on_comment(self, employee_id: str, username: str, comment_time: datetime) -> None:
        connection = self._db.connect()
        with self._db.lock:
            connection.execute(
                """
                INSERT INTO employee_ids (employee_id, first_user, first_time, duplicate_count)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(employee_id) DO UPDATE SET duplicate_count = duplicate_count + 1
                """,
                (employee_id, username, comment_time.isoformat()),
            )
            connection.commit()

    def all(self) -> list[EmployeeIdEntry]:
        connection = self._db.connect()
        rows = connection.execute(
            "SELECT employee_id, first_user, first_time, duplicate_count FROM employee_ids ORDER BY first_time"
        ).fetchall()
        return [
            EmployeeIdEntry(
                employee_id=row["employee_id"],
                first_user=row["first_user"],
                first_time=_parse_dt(row["first_time"]),
                duplicate_count=row["duplicate_count"],
            )
            for row in rows
        ]

    def count(self) -> int:
        connection = self._db.connect()
        row = connection.execute("SELECT COUNT(*) AS n FROM employee_ids").fetchone()
        return int(row["n"])


class WinnerRepository:
    """Persists Lucky Wheel draw results."""

    def __init__(self, db: SQLiteConnectionManager) -> None:
        self._db = db

    def add(self, winner: Winner) -> None:
        connection = self._db.connect()
        with self._db.lock:
            connection.execute(
                """
                INSERT INTO winner_history (winner_name, employee_id, prize, drawn_at)
                VALUES (?, ?, ?, ?)
                """,
                (winner.winner_name, winner.employee_id, winner.prize, winner.drawn_at.isoformat()),
            )
            connection.commit()

    def all(self) -> list[Winner]:
        connection = self._db.connect()
        rows = connection.execute(
            "SELECT winner_name, employee_id, prize, drawn_at FROM winner_history ORDER BY id"
        ).fetchall()
        return [
            Winner(
                winner_name=row["winner_name"],
                employee_id=row["employee_id"],
                prize=row["prize"] or "",
                drawn_at=_parse_dt(row["drawn_at"]),
            )
            for row in rows
        ]


class RepoBundle:
    """Dependency-injection convenience: bundles all repositories built off one connection manager."""

    def __init__(self, db: SQLiteConnectionManager) -> None:
        self.comments = CommentRepository(db)
        self.users = UserRepository(db)
        self.employees = EmployeeRepository(db)
        self.winners = WinnerRepository(db)
