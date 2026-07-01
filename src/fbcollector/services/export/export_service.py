"""On-demand export requests (toolbar buttons), handled off the UI thread."""

import queue
import threading

from fbcollector.core.events import ExportCompleteEvent, ExportRequest, ErrorEvent
from fbcollector.core.queues import QueueBus
from fbcollector.services.export.csv_writer import CsvWriterService
from fbcollector.utils.logger import get_logger

_log = get_logger("export_service")

_KIND_TO_WRITER = {
    "raw": "write_raw_comments",
    "users": "write_unique_users",
    "employees": "write_employee_ids",
    "winners": "write_winner_history",
}


class ExportThread(threading.Thread):
    """Drains ``queue_bus.export_requests`` so a manual export doesn't block the UI
    even mid-session with a large comment volume."""

    def __init__(self, queue_bus: QueueBus, csv_writer: CsvWriterService) -> None:
        super().__init__(name="ExportThread", daemon=True)
        self._queue_bus = queue_bus
        self._csv_writer = csv_writer
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                request: ExportRequest = self._queue_bus.export_requests.get(timeout=0.25)
            except queue.Empty:
                continue
            self._handle(request)

    def _handle(self, request: ExportRequest) -> None:
        method_name = _KIND_TO_WRITER.get(request.kind)
        if method_name is None:
            _log.warning("Unknown export kind: %s", request.kind)
            return
        try:
            path = getattr(self._csv_writer, method_name)()
            row_count = path.read_text(encoding="utf-8-sig").count("\n") - 1
            self._queue_bus.ui_events.put_nowait(
                ExportCompleteEvent(kind=request.kind, path=str(path), row_count=max(row_count, 0))
            )
        except OSError as exc:
            _log.error("Export failed for %s: %s", request.kind, exc)
            self._queue_bus.ui_events.put_nowait(
                ErrorEvent(source="export", message=str(exc), recoverable=True)
            )
