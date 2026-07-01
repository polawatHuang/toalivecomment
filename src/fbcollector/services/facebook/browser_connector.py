"""Playwright CDP connection lifecycle.

Uses Playwright's sync API from inside ``CollectorThread``'s own thread (never on the
Tk main thread, and never mixed with asyncio) since each Playwright sync context is
bound to the thread that created it.
"""

from collections.abc import Callable

from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from fbcollector.constants import CHROME_CDP_URL
from fbcollector.utils.logger import get_logger

_log = get_logger("browser_connector")

_LIVE_URL_HINTS = ("facebook.com/watch", "facebook.com/live", "/videos/")


class BrowserConnector:
    """Owns the Playwright + CDP lifecycle for one collection session."""

    def __init__(self, cdp_url: str = CHROME_CDP_URL) -> None:
        self._cdp_url = cdp_url
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._disconnect_callbacks: list[Callable[[], None]] = []

    def connect(self) -> None:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.connect_over_cdp(self._cdp_url)
        self._browser.on("disconnected", lambda _: self._notify_disconnect())
        _log.info("Attached to Chrome via CDP at %s", self._cdp_url)

    def is_connected(self) -> bool:
        return self._browser is not None and self._browser.is_connected()

    def find_facebook_live_page(self) -> Page | None:
        """Scan open tabs for a Facebook page; prefers URLs that look like a Live/watch page."""
        if self._browser is None:
            return None
        candidates: list[Page] = []
        for context in self._browser.contexts:
            for page in context.pages:
                if "facebook.com" in page.url:
                    candidates.append(page)
        if not candidates:
            return None
        for page in candidates:
            if any(hint in page.url for hint in _LIVE_URL_HINTS):
                return page
        return candidates[0]

    def register_disconnect_callback(self, callback: Callable[[], None]) -> None:
        self._disconnect_callbacks.append(callback)

    def _notify_disconnect(self) -> None:
        _log.warning("Browser disconnected")
        for callback in list(self._disconnect_callbacks):
            callback()

    def disconnect(self) -> None:
        try:
            if self._browser is not None:
                self._browser.close()
        except Exception:  # noqa: BLE001 - best-effort cleanup
            pass
        try:
            if self._playwright is not None:
                self._playwright.stop()
        except Exception:  # noqa: BLE001
            pass
        self._browser = None
        self._playwright = None
