from datetime import datetime

from fbcollector.utils.hashing import comment_hash


def test_same_input_produces_same_hash():
    t = datetime(2026, 1, 1, 10, 30, 0)
    assert comment_hash("alice", "hello world", t) == comment_hash("alice", "hello world", t)


def test_different_username_changes_hash():
    t = datetime(2026, 1, 1, 10, 30, 0)
    assert comment_hash("alice", "hello", t) != comment_hash("bob", "hello", t)


def test_different_text_changes_hash():
    t = datetime(2026, 1, 1, 10, 30, 0)
    assert comment_hash("alice", "hello", t) != comment_hash("alice", "goodbye", t)


def test_time_is_bucketed_to_the_second():
    t1 = datetime(2026, 1, 1, 10, 30, 0, 100000)
    t2 = datetime(2026, 1, 1, 10, 30, 0, 900000)
    assert comment_hash("alice", "hello", t1) == comment_hash("alice", "hello", t2)


def test_different_second_changes_hash():
    t1 = datetime(2026, 1, 1, 10, 30, 0)
    t2 = datetime(2026, 1, 1, 10, 30, 1)
    assert comment_hash("alice", "hello", t1) != comment_hash("alice", "hello", t2)
