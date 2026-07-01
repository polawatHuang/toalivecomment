"""End-to-end queue wiring test using a fake collector/extractor - no real Playwright/Chrome."""

import time
from datetime import datetime

from fbcollector.core.events import CommentBatchEvent
from fbcollector.core.queues import QueueBus
from fbcollector.services.facebook.collector import CollectorThread
from fbcollector.services.storage.models import RawCommentDraft
from fbcollector.services.storage.writer_thread import WriterThread
from fbcollector.utils.id_extractor import EmployeeIdExtractor

_FIXED_TIME = datetime(2026, 1, 1, 9, 0, 0)


class _FakeExtractor:
    """Returns canned draft batches on successive polls, with an overlapping second
    batch to exercise the collector's same-session dedupe."""

    def __init__(self, batches: list[list[RawCommentDraft]]) -> None:
        self._batches = batches
        self._index = 0

    def extract(self, _page):
        if self._index < len(self._batches):
            batch = self._batches[self._index]
            self._index += 1
            return batch
        return []


def _draft(username: str, text: str) -> RawCommentDraft:
    return RawCommentDraft(username=username, comment=text, timestamp=_FIXED_TIME, detected_time=_FIXED_TIME)


def test_collector_dedupes_overlapping_batches_across_polls():
    batch_one = [_draft("alice", "hi"), _draft("bob", "hello")]
    batch_two = [_draft("alice", "hi"), _draft("carol", "hey")]  # "alice/hi" re-scraped, duplicate
    extractor = _FakeExtractor([batch_one, batch_two])
    queue_bus = QueueBus()

    collector = CollectorThread(
        page_provider=lambda: object(),
        extractor=extractor,
        id_extractor=EmployeeIdExtractor(),
        queue_bus=queue_bus,
        poll_interval_ms=10,
    )
    collector.start()
    time.sleep(0.2)
    collector.stop()
    collector.join(timeout=2)

    events = []
    while not queue_bus.ui_events.empty():
        events.append(queue_bus.ui_events.get_nowait())
    batch_events = [e for e in events if isinstance(e, CommentBatchEvent)]

    all_comments = [c for event in batch_events for c in event.comments]
    usernames = sorted(c.username for c in all_comments)
    assert usernames == ["alice", "bob", "carol"]  # duplicate alice/hi suppressed


def test_writer_thread_drains_queue_into_repositories(repos):
    queue_bus = QueueBus()
    from fbcollector.services.export.csv_writer import CsvWriterService

    csv_writer = CsvWriterService(repos, output_dir=None)  # not exercised in this test
    writer = WriterThread(queue_bus, repos, csv_writer)
    writer.start()

    from fbcollector.services.storage.models import RawComment

    comment = RawComment(
        hash="abc123", username="dave", comment="test comment", timestamp=_FIXED_TIME, detected_time=_FIXED_TIME
    )
    queue_bus.raw_comments.put_nowait(comment)

    deadline = time.time() + 2
    while repos.comments.count() == 0 and time.time() < deadline:
        time.sleep(0.05)

    writer.stop()
    writer.join(timeout=2)

    assert repos.comments.count() == 1
    assert repos.users.count() == 1
