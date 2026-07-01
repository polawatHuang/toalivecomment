"""Application logging: rotating file handler plus an in-memory ring buffer for the UI LogPanel."""

import logging
import logging.handlers
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock

from fbcollector.utils.paths import logs_dir

_RING_BUFFER_SIZE = 2000


@dataclass(frozen=True, slots=True)
class LogRecord:
    """A single log line, as displayed in the UI LogPanel."""

    level: str
    message: str
    timestamp: datetime


class RingBufferHandler(logging.Handler):
    """Keeps the last N log records in memory so the UI LogPanel can render them
    without re-reading the log file."""

    def __init__(self, capacity: int = _RING_BUFFER_SIZE) -> None:
        super().__init__()
        self._buffer: deque[LogRecord] = deque(maxlen=capacity)
        self._lock = Lock()

    def emit(self, record: logging.LogRecord) -> None:
        entry = LogRecord(
            level=record.levelname,
            message=record.getMessage(),
            timestamp=datetime.fromtimestamp(record.created),
        )
        with self._lock:
            self._buffer.append(entry)

    def snapshot(self) -> list[LogRecord]:
        with self._lock:
            return list(self._buffer)


_ring_handler: RingBufferHandler | None = None


def setup_logging(log_dir: Path | None = None, level: int = logging.INFO) -> RingBufferHandler:
    """Configure the root ``fbcollector`` logger. Idempotent - safe to call once at startup."""
    global _ring_handler
    if _ring_handler is not None:
        return _ring_handler

    target_dir = log_dir or logs_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = logging.handlers.RotatingFileHandler(
        target_dir / "app.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    ring_handler = RingBufferHandler()
    ring_handler.setFormatter(formatter)

    root = logging.getLogger("fbcollector")
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(ring_handler)

    _ring_handler = ring_handler
    return ring_handler


def get_ring_handler() -> RingBufferHandler | None:
    return _ring_handler


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"fbcollector.{name}")
