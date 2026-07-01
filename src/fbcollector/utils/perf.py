"""Lightweight performance/runtime helpers: memory sampling and time formatting."""

import os
from datetime import timedelta

try:
    import psutil

    _HAS_PSUTIL = True
except ImportError:  # pragma: no cover - psutil is a declared dependency, but degrade gracefully
    _HAS_PSUTIL = False


def current_memory_mb() -> float:
    """Return this process's resident memory usage in megabytes."""
    if _HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return round(process.memory_info().rss / (1024 * 1024), 1)
    return 0.0


def format_running_time(seconds: float) -> str:
    """Format an elapsed-seconds duration as HH:MM:SS."""
    total_seconds = max(0, int(seconds))
    return str(timedelta(seconds=total_seconds))
