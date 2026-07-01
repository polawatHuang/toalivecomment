"""Reads (never mutates) the DOM of a Facebook Live page to pull out visible comments.

BEST-EFFORT / unverified against real Facebook: the JS payload below only queries and
reads text (``querySelectorAll`` + ``innerText``/``getAttribute``); it never calls
``location.reload()``, never touches the <video> element, and never writes to the DOM -
satisfying the spec's "never refresh page / never interfere with video playback"
requirement structurally, regardless of whether the selectors themselves are accurate.
"""

import json
import re
from datetime import datetime

from playwright.sync_api import Page

from fbcollector.services.facebook.selectors import SelectorSet
from fbcollector.services.storage.models import RawCommentDraft


class CommentExtractor:
    """Runs one JS evaluation per poll tick against the live page and parses results in Python."""

    def __init__(self, selectors: SelectorSet) -> None:
        self._selectors = selectors
        self._aria_pattern = re.compile(selectors.aria_label_pattern)

    def build_eval_script(self) -> str:
        """Pure read-only DOM query: returns a list of raw text/attribute payloads.
        Username/comment splitting happens in Python (see ``_parse_raw``) so the JS
        stays trivial to eyeball for safety (read-only) even without a live page to test.
        """
        selectors_json = json.dumps(
            {
                "container": self._selectors.comment_container,
                "usernameSelectors": self._selectors.username_selectors,
                "textSelectors": self._selectors.text_selectors,
            }
        )
        return f"""
        (() => {{
            const s = {selectors_json};
            const results = [];
            const nodes = document.querySelectorAll(s.container);
            nodes.forEach((node, idx) => {{
                let username = "";
                for (const sel of s.usernameSelectors) {{
                    const el = node.querySelector(sel);
                    if (el && el.innerText && el.innerText.trim()) {{ username = el.innerText.trim(); break; }}
                }}
                let text = "";
                for (const sel of s.textSelectors) {{
                    const el = node.querySelector(sel);
                    if (el && el.innerText && el.innerText.trim()) {{ text = el.innerText.trim(); break; }}
                }}
                const ariaLabel = node.getAttribute('aria-label') || "";
                const anchor = node.querySelector('a[href*="/user/"], a[href*="/profile.php"], a[role="link"]');
                const profileUrl = anchor ? anchor.href : "";
                const commentId = node.id || node.getAttribute('data-commentid') || String(idx);
                results.push({{username, text, ariaLabel, profileUrl, commentId}});
            }});
            return results;
        }})()
        """

    def extract(self, page: Page) -> list[RawCommentDraft]:
        now = datetime.now()
        raw_results = page.evaluate(self.build_eval_script())
        drafts: list[RawCommentDraft] = []
        for item in raw_results:
            draft = self._parse_raw(item, now)
            if draft is not None:
                drafts.append(draft)
        return drafts

    def _parse_raw(self, item: dict, detected_time: datetime) -> RawCommentDraft | None:
        username = (item.get("username") or "").strip()
        text = (item.get("text") or "").strip()

        if not username or not text:
            # heuristic, best-effort: fall back to parsing the aria-label pattern
            aria_label = (item.get("ariaLabel") or "").strip()
            match = self._aria_pattern.match(aria_label)
            if match:
                username = username or match.group("username").strip()
                text = text or match.group("comment").strip()

        if not username or not text:
            return None

        return RawCommentDraft(
            username=username,
            comment=text,
            timestamp=detected_time,
            detected_time=detected_time,
            comment_id=item.get("commentId") or None,
            profile_url=item.get("profileUrl") or None,
        )
