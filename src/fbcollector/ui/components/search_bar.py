"""Debounced search box for realtime filtering of the live comment feed."""

from collections.abc import Callable

import customtkinter as ctk

from fbcollector.ui import theme

_DEBOUNCE_MS = 200


class SearchBar(ctk.CTkFrame):
    """Fires ``on_query_changed(text)`` after the user pauses typing, not on every keystroke."""

    def __init__(self, master, on_query_changed: Callable[[str], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self._on_query_changed = on_query_changed
        self._debounce_job: str | None = None

        self._entry = ctk.CTkEntry(
            self,
            placeholder_text="Search user, employee ID, or comment...",
            corner_radius=theme.BUTTON_RADIUS,
            height=36,
        )
        self._entry.pack(fill="x", padx=4)
        self._entry.bind("<KeyRelease>", self._on_key_release)

    def _on_key_release(self, _event) -> None:
        if self._debounce_job is not None:
            self.after_cancel(self._debounce_job)
        self._debounce_job = self.after(_DEBOUNCE_MS, self._fire)

    def _fire(self) -> None:
        self._debounce_job = None
        self._on_query_changed(self._entry.get().strip())

    def clear(self) -> None:
        self._entry.delete(0, "end")
