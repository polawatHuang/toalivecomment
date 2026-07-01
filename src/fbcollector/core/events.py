"""Event dataclasses that cross the worker-thread -> UI-thread boundary.

These are pure data: no behavior, no references to Tk widgets. Worker threads construct
these and put them on ``QueueBus.ui_events``; only ``MainWindow._drain_queue`` reads them.
"""

from dataclasses import dataclass, field
from datetime import datetime

from fbcollector.services.storage.models import RawComment, Winner


@dataclass(frozen=True, slots=True)
class UIEvent:
    """Marker base class for anything that can be dispatched on the UI thread."""


@dataclass(frozen=True, slots=True)
class CommentBatchEvent(UIEvent):
    comments: list[RawComment]


@dataclass(frozen=True, slots=True)
class StatsEvent(UIEvent):
    total_comments: int
    unique_users: int
    employee_ids: int
    comments_per_second: float
    running_seconds: float
    memory_mb: float
    duplicate_users: int = 0
    duplicate_ids: int = 0


@dataclass(frozen=True, slots=True)
class ConnectionStatusEvent(UIEvent):
    chrome_connected: bool
    facebook_detected: bool
    message: str


@dataclass(frozen=True, slots=True)
class LogEvent(UIEvent):
    level: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True, slots=True)
class ExportCompleteEvent(UIEvent):
    kind: str
    path: str
    row_count: int


@dataclass(frozen=True, slots=True)
class WheelResultEvent(UIEvent):
    winner: Winner


@dataclass(frozen=True, slots=True)
class ErrorEvent(UIEvent):
    source: str
    message: str
    recoverable: bool = True


@dataclass(frozen=True, slots=True)
class SessionResetEvent(UIEvent):
    """Fired after Clear Session so the dashboard/live feed can reset themselves."""


@dataclass(frozen=True, slots=True)
class SettingsChangedEvent(UIEvent):
    """Fired after settings are saved, so hot-swappable services can pick up new values."""


# --- Non-UI command/request payloads (still pure data, travel the other direction) ---


@dataclass(frozen=True, slots=True)
class ExportRequest:
    kind: str  # "raw" | "users" | "employees" | "winners"


@dataclass(frozen=True, slots=True)
class WheelCommand:
    kind: str  # "import_csv" | "record_winner"
    payload: object = None
