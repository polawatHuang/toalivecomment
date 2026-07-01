"""Stable content hashing used for comment de-duplication."""

import hashlib
from datetime import datetime


def _bucket_to_second(moment: datetime) -> str:
    """Round a timestamp down to the nearest second.

    Facebook's DOM sometimes re-renders the same comment node (e.g. after a reflow),
    which produces a fresh Python ``datetime.now()`` on re-detection even though the
    comment itself hasn't changed. Bucketing to the second keeps the hash stable across
    such re-renders while still distinguishing genuinely different comments posted in the
    same second by the same user (extremely rare, and the SQLite UNIQUE constraint on
    hash means such a rare collision is simply treated as a duplicate - an acceptable
    tradeoff for realtime dedupe).
    """
    return moment.replace(microsecond=0).isoformat()


def comment_hash(username: str, comment_text: str, detected_time: datetime) -> str:
    """Compute a stable SHA-1 hex digest identifying a single comment occurrence."""
    payload = "\x1f".join((username.strip(), comment_text.strip(), _bucket_to_second(detected_time)))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()
