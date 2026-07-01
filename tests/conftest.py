"""Shared pytest fixtures."""

from datetime import datetime

import pytest

from fbcollector.services.storage.db import SQLiteConnectionManager
from fbcollector.services.storage.models import RawComment
from fbcollector.services.storage.repositories import RepoBundle


@pytest.fixture
def db(tmp_path):
    manager = SQLiteConnectionManager(tmp_path / "test_session.sqlite3")
    manager.initialize_schema()
    yield manager
    manager.close()


@pytest.fixture
def repos(db):
    return RepoBundle(db)


@pytest.fixture
def sample_comments() -> list[RawComment]:
    now = datetime(2026, 1, 1, 12, 0, 0)
    return [
        RawComment(
            hash=f"hash-{i}",
            username=f"user{i % 3}",
            comment=f"comment number {i}",
            timestamp=now,
            detected_time=now,
            employee_id=None,
        )
        for i in range(5)
    ]
