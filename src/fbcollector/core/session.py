"""Orchestrates Start/Pause/Stop/Clear Session - the service layer the UI calls into.

``MainWindow`` never talks to ``CollectorThread``, repositories, or Playwright directly;
every button handler goes through ``SessionController``. This keeps the UI layer a thin
presentation layer and the threading/reconnect complexity in one well-tested place.
"""

import threading
import time

from fbcollector.constants import RECONNECT_MAX_BACKOFF_SECONDS, RECONNECT_RETRY_DELAY_SECONDS
from fbcollector.core.events import ConnectionStatusEvent, LogEvent, SessionResetEvent
from fbcollector.core.queues import QueueBus
from fbcollector.core.thread_manager import ThreadManager
from fbcollector.services.export.csv_writer import CsvWriterService
from fbcollector.services.export.export_service import ExportThread
from fbcollector.services.facebook.browser_connector import BrowserConnector
from fbcollector.services.facebook.chrome_manager import ChromeManager, ChromeNotFoundError
from fbcollector.services.facebook.collector import CollectorThread
from fbcollector.services.facebook.comment_extractor import CommentExtractor
from fbcollector.services.facebook.selectors import SelectorSet
from fbcollector.services.settings_service import Settings, SettingsService
from fbcollector.services.storage.db import SQLiteConnectionManager
from fbcollector.services.storage.repositories import RepoBundle
from fbcollector.services.storage.writer_thread import WriterThread
from fbcollector.utils.id_extractor import EmployeeIdExtractor
from fbcollector.utils.logger import get_logger

_log = get_logger("session")

_FACEBOOK_PAGE_WAIT_TIMEOUT_SECONDS = 60.0
_FACEBOOK_PAGE_POLL_INTERVAL_SECONDS = 1.0


class SessionController:
    """Owns the full lifecycle: managed Chrome -> CDP attach -> collector/writer/export
    threads -> autosave -> teardown. One instance per running session."""

    def __init__(
        self,
        queue_bus: QueueBus,
        db: SQLiteConnectionManager,
        repos: RepoBundle,
        csv_writer: CsvWriterService,
        settings_service: SettingsService,
        selectors: SelectorSet,
    ) -> None:
        self._queue_bus = queue_bus
        self._db = db
        self._repos = repos
        self._csv_writer = csv_writer
        self._settings_service = settings_service
        self._selectors = selectors

        self._chrome = ChromeManager()
        self._browser = BrowserConnector()
        self._thread_manager = ThreadManager()
        self._collector: CollectorThread | None = None
        self._writer: WriterThread | None = None
        self._exporter: ExportThread | None = None
        self._autosave_stop = threading.Event()
        self._autosave_thread: threading.Thread | None = None

        self._cached_page = None
        self._paused = threading.Event()
        self._running = False
        self._start_time: float | None = None
        self._reconnect_lock = threading.Lock()

    # --- lifecycle -----------------------------------------------------------------

    def start(self) -> None:
        """Blocking: run the full CONNECT sequence. Call from a background thread, not
        the Tk main thread - this performs process launch and network I/O."""
        settings = self._settings_service.load()
        self._emit_status(False, False, "Launching Chrome...")
        try:
            self._chrome.launch()
        except ChromeNotFoundError as exc:
            self._emit_status(False, False, str(exc))
            self._emit_log("ERROR", str(exc))
            return

        if not self._chrome.wait_until_debug_port_ready():
            self._emit_status(False, False, "Chrome did not open its debug port in time.")
            self._emit_log("ERROR", "Timed out waiting for Chrome's remote debugging port.")
            return

        self._emit_status(True, False, "Chrome launched. Connecting via CDP...")
        self._browser.connect()
        self._browser.register_disconnect_callback(self._on_browser_disconnected)
        self._emit_status(True, False, "Waiting for your Facebook Live page...")

        page = self._wait_for_facebook_page()
        if page is None:
            self._emit_status(True, False, "No Facebook page detected yet - still watching.")
        else:
            self._cached_page = page
            self._emit_status(True, True, "Facebook Live page detected. Monitoring comments.")
            self._emit_log("INFO", f"Attached to Facebook page: {page.url}")

        self._start_worker_threads(settings)
        self._running = True
        self._start_time = time.monotonic()

    def _wait_for_facebook_page(self, timeout_seconds: float = _FACEBOOK_PAGE_WAIT_TIMEOUT_SECONDS):
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            page = self._browser.find_facebook_live_page()
            if page is not None:
                return page
            time.sleep(_FACEBOOK_PAGE_POLL_INTERVAL_SECONDS)
        return None

    def _start_worker_threads(self, settings: Settings) -> None:
        id_extractor = EmployeeIdExtractor(settings.employee_id_regex)
        extractor = CommentExtractor(self._selectors)

        self._collector = CollectorThread(
            page_provider=self._current_page,
            extractor=extractor,
            id_extractor=id_extractor,
            queue_bus=self._queue_bus,
            on_poll_error=self._on_collector_error,
        )
        self._writer = WriterThread(self._queue_bus, self._repos, self._csv_writer)
        self._exporter = ExportThread(self._queue_bus, self._csv_writer)

        self._thread_manager.register("collector", self._collector)
        self._thread_manager.register("writer", self._writer)
        self._thread_manager.register("exporter", self._exporter)
        self._thread_manager.start_all()

        self._autosave_stop.clear()
        self._autosave_thread = threading.Thread(
            target=self._csv_writer.start_autosave_loop, args=(self._autosave_stop,), daemon=True
        )
        self._autosave_thread.start()

    def _current_page(self):
        if self._paused.is_set():
            return None
        return self._cached_page

    def pause(self) -> None:
        self._paused.set()
        self._emit_log("INFO", "Collection paused.")

    def resume(self) -> None:
        self._paused.clear()
        self._emit_log("INFO", "Collection resumed.")

    def stop(self) -> None:
        self._autosave_stop.set()
        self._thread_manager.stop_all()
        self._browser.disconnect()
        self._chrome.terminate()
        self._running = False
        self._emit_status(False, False, "Disconnected.")
        self._emit_log("INFO", "Session stopped.")

    def clear_session(self) -> None:
        self._db.reset()
        self._emit_log("INFO", "Session cleared.")
        self._queue_bus.ui_events.put_nowait(SessionResetEvent())

    def shutdown(self) -> None:
        """Called on app exit: stop threads, flush CSV, close DB, terminate managed Chrome."""
        if self._running:
            self.stop()
        try:
            self._csv_writer.write_raw_comments()
            self._csv_writer.write_unique_users()
            self._csv_writer.write_employee_ids()
        except OSError:
            _log.exception("Failed to flush CSV on shutdown")
        self._db.close()

    # --- reconnect -------------------------------------------------------------------

    def _on_browser_disconnected(self) -> None:
        self._emit_status(False, False, "Chrome disconnected. Attempting to reconnect...")
        threading.Thread(target=self._reconnect, daemon=True).start()

    def _on_collector_error(self, exc: Exception) -> None:
        _log.warning("Collector poll error: %s", exc)
        self._emit_log("WARN", f"Collector error, attempting reconnect: {exc}")
        threading.Thread(target=self._reconnect, daemon=True).start()

    def _reconnect(self) -> None:
        if not self._reconnect_lock.acquire(blocking=False):
            return  # a reconnect attempt is already in progress
        try:
            backoff = RECONNECT_RETRY_DELAY_SECONDS
            while self._thread_manager.is_alive("collector"):
                self._emit_status(False, False, "Reconnecting...")
                try:
                    if not self._chrome.is_running():
                        self._chrome.launch()
                        self._chrome.wait_until_debug_port_ready()
                    self._browser.disconnect()
                    self._browser.connect()
                    self._browser.register_disconnect_callback(self._on_browser_disconnected)
                    page = self._wait_for_facebook_page(timeout_seconds=10.0)
                    if page is not None:
                        self._cached_page = page
                        self._emit_status(True, True, "Reconnected.")
                        self._emit_log("INFO", "Reconnected to Facebook Live page.")
                        return
                    self._emit_status(True, False, "Reconnected to Chrome, waiting for Facebook page...")
                    return
                except Exception as exc:  # noqa: BLE001 - keep retrying regardless of failure mode
                    _log.warning("Reconnect attempt failed: %s", exc)
                    time.sleep(backoff)
                    backoff = min(backoff * 2, RECONNECT_MAX_BACKOFF_SECONDS)
        finally:
            self._reconnect_lock.release()

    # --- helpers -----------------------------------------------------------------

    def _emit_status(self, chrome_connected: bool, facebook_detected: bool, message: str) -> None:
        self._queue_bus.ui_events.put_nowait(
            ConnectionStatusEvent(
                chrome_connected=chrome_connected, facebook_detected=facebook_detected, message=message
            )
        )

    def _emit_log(self, level: str, message: str) -> None:
        self._queue_bus.ui_events.put_nowait(LogEvent(level=level, message=message))

    @property
    def running_seconds(self) -> float:
        if self._start_time is None:
            return 0.0
        return time.monotonic() - self._start_time

    @property
    def is_running(self) -> bool:
        return self._running
