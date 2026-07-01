"""Main application window: the shell, the queue pump, and all button wiring.

``MainWindow`` never talks to worker threads, Playwright, or repositories for writes
directly - it calls into ``SessionController`` (the service layer) and only reads
repositories for periodic stat refreshes. ``_drain_queue`` is the *only* place a
worker-thread-originated event is turned into a widget mutation.
"""

import threading
from pathlib import Path

import customtkinter as ctk

from fbcollector.constants import UI_QUEUE_MAX_EVENTS_PER_TICK, UI_QUEUE_POLL_MS
from fbcollector.core.events import (
    CommentBatchEvent,
    ConnectionStatusEvent,
    ErrorEvent,
    ExportCompleteEvent,
    LogEvent,
    SessionResetEvent,
    SettingsChangedEvent,
    UIEvent,
)
from fbcollector.core.queues import QueueBus
from fbcollector.core.session import SessionController
from fbcollector.services.export.csv_writer import CsvWriterService
from fbcollector.services.settings_service import Settings, SettingsService
from fbcollector.services.storage.repositories import RepoBundle
from fbcollector.ui import theme
from fbcollector.ui.components.connect_flow import ConnectDialog
from fbcollector.ui.components.dashboard_cards import DashboardPanel
from fbcollector.ui.components.log_panel import LogPanel
from fbcollector.ui.components.live_feed import LiveFeedView
from fbcollector.ui.components.search_bar import SearchBar
from fbcollector.ui.components.settings_dialog import SettingsDialog
from fbcollector.ui.components.toolbar import BottomToolbar, ToolbarCallbacks
from fbcollector.ui.components.top_nav import TopNavBar
from fbcollector.ui.wheel_window import WheelWindow
from fbcollector.utils.perf import current_memory_mb


class MainWindow(ctk.CTk):
    """Top-level application shell."""

    def __init__(
        self,
        queue_bus: QueueBus,
        session: SessionController,
        settings_service: SettingsService,
        selectors_path: Path,
        repos: RepoBundle,
        csv_writer: CsvWriterService,
    ) -> None:
        super().__init__(fg_color=theme.BG_ROOT)
        self._queue_bus = queue_bus
        self._session = session
        self._settings_service = settings_service
        self._selectors_path = selectors_path
        self._repos = repos
        self._csv_writer = csv_writer
        self._settings: Settings = settings_service.load()

        self._connect_dialog: ConnectDialog | None = None
        self._last_total_comments = 0

        self.title("Facebook Live Collector Pro - Enterprise Edition")
        self.geometry("1280x800")
        self.minsize(1024, 680)

        self._build_layout()
        self._start_event_pump()
        self._start_stats_loop()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # --- layout ------------------------------------------------------------------

    def _build_layout(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.top_nav = TopNavBar(self, self._on_toggle_theme, self._open_settings)
        self.top_nav.grid(row=0, column=0, sticky="ew")

        self.dashboard = DashboardPanel(self)
        self.dashboard.grid(row=1, column=0, sticky="ew", padx=12, pady=(12, 4))

        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=2, column=0, sticky="nsew", padx=12, pady=4)
        center.grid_rowconfigure(1, weight=1)
        center.grid_columnconfigure(0, weight=1)

        self.search_bar = SearchBar(center, self._on_search)
        self.search_bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self.live_feed = LiveFeedView(center, on_scroll_page=self._repos.comments.fetch_page)
        self.live_feed.grid(row=1, column=0, sticky="nsew")

        self.log_panel = LogPanel(self)
        self.log_panel.grid(row=3, column=0, sticky="ew")

        callbacks = ToolbarCallbacks(
            on_start=self._on_start,
            on_pause=self._on_pause,
            on_stop=self._on_stop,
            on_export_raw=lambda: self._on_export("raw"),
            on_export_users=lambda: self._on_export("users"),
            on_export_employees=lambda: self._on_export("employees"),
            on_lucky_wheel=self._open_wheel,
            on_clear_session=self._on_clear_session,
        )
        self.toolbar = BottomToolbar(self, callbacks)
        self.toolbar.grid(row=4, column=0, sticky="ew")
        self.toolbar.set_running_state(False)

    # --- queue pump ----------------------------------------------------------------

    def _start_event_pump(self) -> None:
        self.after(UI_QUEUE_POLL_MS, self._drain_queue)

    def _drain_queue(self) -> None:
        for _ in range(UI_QUEUE_MAX_EVENTS_PER_TICK):
            try:
                event: UIEvent = self._queue_bus.ui_events.get_nowait()
            except Exception:
                break
            self._dispatch(event)
        self.after(UI_QUEUE_POLL_MS, self._drain_queue)

    def _dispatch(self, event: UIEvent) -> None:
        if isinstance(event, CommentBatchEvent):
            self.live_feed.append_batch(event.comments)
        elif isinstance(event, ConnectionStatusEvent):
            self.top_nav.status_pill.update_status(event)
            self.dashboard.update_connection(event)
            if self._connect_dialog is not None and self._connect_dialog.winfo_exists():
                self._connect_dialog.update_status(event)
        elif isinstance(event, LogEvent):
            self.log_panel.append(event)
        elif isinstance(event, ExportCompleteEvent):
            self.log_panel.append(
                LogEvent(level="INFO", message=f"Export finished: {event.kind} -> {event.path}")
            )
        elif isinstance(event, ErrorEvent):
            self.log_panel.append(LogEvent(level="ERROR", message=f"[{event.source}] {event.message}"))
        elif isinstance(event, SessionResetEvent):
            self.live_feed.reset()
            self.dashboard.reset()
        elif isinstance(event, SettingsChangedEvent):
            self._settings = self._settings_service.load()

    # --- periodic stats --------------------------------------------------------------

    def _start_stats_loop(self) -> None:
        self.after(1000, self._update_stats)

    def _update_stats(self) -> None:
        from fbcollector.core.events import StatsEvent

        total = self._repos.comments.count()
        delta = max(0, total - self._last_total_comments)
        self._last_total_comments = total
        stats = StatsEvent(
            total_comments=total,
            unique_users=self._repos.users.count(),
            employee_ids=self._repos.employees.count(),
            comments_per_second=float(delta),
            running_seconds=self._session.running_seconds,
            memory_mb=current_memory_mb(),
        )
        self.dashboard.update_stats(stats)
        self.after(1000, self._update_stats)

    # --- button handlers -------------------------------------------------------------

    def _on_toggle_theme(self, is_dark: bool) -> None:
        theme.apply_appearance("dark" if is_dark else "light")

    def _on_start(self) -> None:
        self._connect_dialog = ConnectDialog(self, on_cancel=self._on_stop)
        threading.Thread(target=self._session.start, daemon=True).start()
        self.toolbar.set_running_state(True)

    def _on_pause(self) -> None:
        self._session.pause()

    def _on_stop(self) -> None:
        threading.Thread(target=self._session.stop, daemon=True).start()
        self.toolbar.set_running_state(False)

    def _on_export(self, kind: str) -> None:
        from fbcollector.core.events import ExportRequest

        self._queue_bus.export_requests.put_nowait(ExportRequest(kind=kind))

    def _on_clear_session(self) -> None:
        self._session.clear_session()

    def _on_search(self, query: str) -> None:
        self.live_feed.apply_filter(query)

    def _open_settings(self) -> None:
        SettingsDialog(
            self,
            self._settings_service,
            self._selectors_path,
            on_saved=self._on_settings_saved,
            on_selectors_reloaded=self._on_selectors_reloaded,
        )

    def _on_settings_saved(self, settings: Settings) -> None:
        self._settings = settings
        theme.apply_appearance(settings.theme)
        self._csv_writer.set_output_dir(Path(settings.csv_folder))
        self.log_panel.append(LogEvent(level="INFO", message="Settings saved."))

    def _on_selectors_reloaded(self) -> None:
        self.log_panel.append(LogEvent(level="INFO", message="Selectors reloaded."))

    def _open_wheel(self) -> None:
        WheelWindow(self, repos=self._repos, csv_writer=self._csv_writer)

    def _on_close(self) -> None:
        self._session.shutdown()
        self.destroy()
