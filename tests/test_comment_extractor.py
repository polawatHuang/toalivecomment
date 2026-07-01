"""Tests CommentExtractor's parsing logic against a hand-written static HTML fixture.

This validates the *parser*, not real-Facebook selector accuracy - there is no live
Facebook page available to verify against. Skipped automatically if Playwright's
Chromium browser isn't installed in this environment (e.g. offline CI), since spinning
up a headless browser is the only way to exercise real DOM querying/evaluate().
"""

from pathlib import Path

import pytest

from fbcollector.services.facebook.comment_extractor import CommentExtractor
from fbcollector.services.facebook.selectors import default_selector_set

playwright_sync_api = pytest.importorskip("playwright.sync_api")

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "facebook_comments.html"


@pytest.fixture
def fixture_page():
    try:
        with playwright_sync_api.sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(_FIXTURE_PATH.as_uri())
            yield page
            browser.close()
    except Exception as exc:  # noqa: BLE001 - no browser binary installed, skip gracefully
        pytest.skip(f"Playwright Chromium not available in this environment: {exc}")


def test_extractor_parses_fixture_comments(fixture_page):
    extractor = CommentExtractor(default_selector_set())
    drafts = extractor.extract(fixture_page)

    usernames = {d.username for d in drafts}
    assert "Jane Doe" in usernames
    assert "John Smith" in usernames

    john = next(d for d in drafts if d.username == "John Smith")
    assert "123456" in john.comment
