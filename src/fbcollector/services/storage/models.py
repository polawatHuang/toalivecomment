"""Plain data models shared by the SQLite repositories and the CSV writers.

Each dataclass owns its ``to_csv_row``/``csv_headers`` so column order has exactly one
source of truth instead of being duplicated between the writer and the schema.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RawCommentDraft:
    """A comment as freshly scraped, before it has been assigned a stable hash/employee id."""

    username: str
    comment: str
    timestamp: datetime
    detected_time: datetime
    comment_id: str | None = None
    profile_url: str | None = None


@dataclass(frozen=True, slots=True)
class RawComment:
    """A comment persisted to storage: draft data plus derived hash and employee id."""

    hash: str
    username: str
    comment: str
    timestamp: datetime
    detected_time: datetime
    employee_id: str | None = None

    @staticmethod
    def csv_headers() -> list[str]:
        return ["Timestamp", "Username", "Comment", "EmployeeID"]

    def to_csv_row(self) -> list[str]:
        return [self.timestamp.isoformat(sep=" "), self.username, self.comment, self.employee_id or ""]


@dataclass(frozen=True, slots=True)
class UniqueUser:
    """First-occurrence-deduplicated user entry."""

    username: str
    first_comment_time: datetime
    comment_count: int

    @staticmethod
    def csv_headers() -> list[str]:
        return ["Username", "First Comment Time", "Comment Count"]

    def to_csv_row(self) -> list[str]:
        return [self.username, self.first_comment_time.isoformat(sep=" "), str(self.comment_count)]


@dataclass(frozen=True, slots=True)
class EmployeeIdEntry:
    """First-occurrence-deduplicated employee ID entry."""

    employee_id: str
    first_user: str
    first_time: datetime
    duplicate_count: int

    @staticmethod
    def csv_headers() -> list[str]:
        return ["EmployeeID", "First User", "Time", "Duplicate Count"]

    def to_csv_row(self) -> list[str]:
        return [self.employee_id, self.first_user, self.first_time.isoformat(sep=" "), str(self.duplicate_count)]


@dataclass(frozen=True, slots=True)
class Winner:
    """A single Lucky Wheel draw result."""

    winner_name: str
    employee_id: str | None
    prize: str
    drawn_at: datetime

    @staticmethod
    def csv_headers() -> list[str]:
        return ["Winner", "EmployeeID", "Prize", "Time"]

    def to_csv_row(self) -> list[str]:
        return [self.winner_name, self.employee_id or "", self.prize, self.drawn_at.isoformat(sep=" ")]
