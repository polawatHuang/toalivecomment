"""Polls the attached Facebook page every N milliseconds and emits only NEW comments."""

import threading
from collections.abc import Callable

from playwright.sync_api import Page

from fbcollector.constants import DEFAULT_POLL_INTERVAL_MS
from fbcollector.core.events import CommentBatchEvent
from fbcollector.core.queues import QueueBus
from fbcollector.services.facebook.comment_extractor import CommentExtractor
from fbcollector.utils.hashing import comment_hash
from fbcollector.utils.id_extractor import EmployeeIdExtractor
from fbcollector.utils.logger import get_logger
from fbcollector.services.storage.models import RawComment

_log = get_logger("collector")


class CollectorThread(threading.Thread):
    """Polls every ``poll_interval_ms``, dedupes by content hash, and pushes new
    ``RawComment`` objects onto ``queue_bus.raw_comments`` plus a lightweight
    ``CommentBatchEvent`` onto ``queue_bus.ui_events`` for the live feed.

    Dedupe is two-layered: an in-memory ``set[str]`` here gives O(1) same-session
    filtering (cheap, resets on reconnect), while ``CommentRepository.insert_batch``'s
    SQLite ``UNIQUE(hash)`` constraint is the authoritative backstop that survives a
    reconnect resetting this in-memory set.
    """

    def __init__(
        self,
        page_provider: Callable[[], Page | None],
        extractor: CommentExtractor,
        id_extractor: EmployeeIdExtractor,
        queue_bus: QueueBus,
        on_poll_error: Callable[[Exception], None] | None = None,
        poll_interval_ms: int = DEFAULT_POLL_INTERVAL_MS,
    ) -> None:
        super().__init__(name="CollectorThread", daemon=True)
        self._page_provider = page_provider
        self._extractor = extractor
        self._id_extractor = id_extractor
        self._queue_bus = queue_bus
        self._on_poll_error = on_poll_error
        self._poll_interval_ms = poll_interval_ms
        self._stop_event = threading.Event()
        self._seen_hashes: set[str] = set()

    def stop(self) -> None:
        self._stop_event.set()

    def set_employee_id_extractor(self, extractor: EmployeeIdExtractor) -> None:
        """Hot-swap the extractor when Settings changes the regex, without restarting the thread."""
        self._id_extractor = extractor

    def set_comment_extractor(self, extractor: CommentExtractor) -> None:
        """Hot-swap after a selector reload from Settings."""
        self._extractor = extractor

    def run(self) -> None:
        while not self._stop_event.is_set():
            page = self._page_provider()
            if page is not None:
                self._poll_once(page)
            self._stop_event.wait(self._poll_interval_ms / 1000)

    def _poll_once(self, page: Page) -> None:
        try:
            drafts = self._extractor.extract(page)
        except Exception as exc:  # noqa: BLE001 - any Playwright/JS error triggers reconnect handling
            if self._on_poll_error is not None:
                self._on_poll_error(exc)
            return

        new_comments: list[RawComment] = []
        for draft in drafts:
            content_hash = comment_hash(draft.username, draft.comment, draft.detected_time)
            if content_hash in self._seen_hashes:
                continue
            self._seen_hashes.add(content_hash)
            employee_id = self._id_extractor.extract(draft.comment)
            new_comments.append(
                RawComment(
                    hash=content_hash,
                    username=draft.username,
                    comment=draft.comment,
                    timestamp=draft.timestamp,
                    detected_time=draft.detected_time,
                    employee_id=employee_id,
                )
            )

        if new_comments:
            for comment in new_comments:
                self._queue_bus.raw_comments.put_nowait(comment)
            self._queue_bus.ui_events.put_nowait(CommentBatchEvent(comments=new_comments))
            _log.debug("Detected %d new comment(s)", len(new_comments))
