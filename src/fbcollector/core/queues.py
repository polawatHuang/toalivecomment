"""Central queue registry shared across threads.

A single ``QueueBus`` instance is created once in ``app.py`` and passed by constructor
injection to every thread/service that needs it - deliberately not a module-level
singleton, so there is no global mutable state and tests can construct isolated buses.
"""

import queue

from fbcollector.core.events import ExportRequest, UIEvent, WheelCommand
from fbcollector.services.storage.models import RawComment


class QueueBus:
    """Named ``queue.Queue`` registry for cross-thread communication."""

    def __init__(self) -> None:
        self.ui_events: queue.Queue[UIEvent] = queue.Queue()
        self.raw_comments: queue.Queue[RawComment] = queue.Queue()
        self.export_requests: queue.Queue[ExportRequest] = queue.Queue()
        self.wheel_commands: queue.Queue[WheelCommand] = queue.Queue()
