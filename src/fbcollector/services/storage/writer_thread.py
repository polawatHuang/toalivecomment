"""Writer thread: batches raw comments from the queue into SQLite, keeping the UI thread free."""

import queue
import threading
import time

from fbcollector.constants import WRITER_BATCH_MAX_ITEMS, WRITER_BATCH_TIMEOUT_SECONDS
from fbcollector.core.queues import QueueBus
from fbcollector.services.export.csv_writer import CsvWriterService
from fbcollector.services.storage.models import RawComment
from fbcollector.services.storage.repositories import RepoBundle
from fbcollector.utils.logger import get_logger

_log = get_logger("writer_thread")


class WriterThread(threading.Thread):
    """Drains ``queue_bus.raw_comments``, writes to SQLite in batches (executemany, one
    transaction per drain cycle - up to ``WRITER_BATCH_MAX_ITEMS`` rows or
    ``WRITER_BATCH_TIMEOUT_SECONDS`` whichever comes first), updates the user/employee
    repositories, and marks the CSV writer dirty for the next autosave tick.
    """

    def __init__(self, queue_bus: QueueBus, repos: RepoBundle, csv_writer: CsvWriterService) -> None:
        super().__init__(name="WriterThread", daemon=True)
        self._queue_bus = queue_bus
        self._repos = repos
        self._csv_writer = csv_writer
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.is_set():
            batch = self._drain_up_to(WRITER_BATCH_MAX_ITEMS, WRITER_BATCH_TIMEOUT_SECONDS)
            if not batch:
                continue
            self._process_batch(batch)

    def _drain_up_to(self, max_items: int, timeout: float) -> list[RawComment]:
        batch: list[RawComment] = []
        deadline = time.monotonic() + timeout
        while len(batch) < max_items:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                item = self._queue_bus.raw_comments.get(timeout=remaining)
            except queue.Empty:
                break
            batch.append(item)
        return batch

    def _process_batch(self, batch: list[RawComment]) -> None:
        try:
            self._repos.comments.insert_batch(batch)
            for comment in batch:
                self._repos.users.upsert_on_comment(comment.username, comment.timestamp)
                if comment.employee_id:
                    self._repos.employees.upsert_on_comment(
                        comment.employee_id, comment.username, comment.timestamp
                    )
            self._csv_writer.mark_dirty()
        except Exception:  # noqa: BLE001 - writer thread must never die from a bad batch
            _log.exception("Failed to process comment batch of size %d", len(batch))
