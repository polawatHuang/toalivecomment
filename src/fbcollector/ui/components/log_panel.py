"""Collapsible application log strip (connection, errors, CSV saved, export finished, reconnect)."""

import customtkinter as ctk

from fbcollector.core.events import LogEvent
from fbcollector.ui import theme

_MAX_VISIBLE_LINES = 300

_LEVEL_COLORS = {
    "ERROR": theme.DANGER,
    "WARN": theme.WARNING,
    "WARNING": theme.WARNING,
    "INFO": theme.TEXT_SECONDARY,
    "DEBUG": theme.TEXT_MUTED,
}


class LogPanel(ctk.CTkFrame):
    """A collapsible textbox tailing the most recent application log lines."""

    def __init__(self, master) -> None:
        super().__init__(master, corner_radius=0, fg_color=theme.BG_SURFACE)
        self._expanded = True

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(4, 0))
        ctk.CTkLabel(header, text="Application Log", font=theme.body_font(11, "bold")).pack(side="left")
        self._toggle_button = ctk.CTkButton(
            header, text="▾", width=24, height=20, command=self._toggle, fg_color="transparent"
        )
        self._toggle_button.pack(side="right")

        self._textbox = ctk.CTkTextbox(self, height=110, font=theme.mono_font(11), wrap="none")
        self._textbox.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self._textbox.configure(state="disabled")
        self._line_count = 0

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        if self._expanded:
            self._textbox.pack(fill="both", expand=True, padx=12, pady=(0, 8))
            self._toggle_button.configure(text="▾")
        else:
            self._textbox.pack_forget()
            self._toggle_button.configure(text="▸")

    def append(self, event: LogEvent) -> None:
        line = f"{event.timestamp:%H:%M:%S} [{event.level}] {event.message}\n"
        self._textbox.configure(state="normal")
        self._textbox.insert("end", line)
        self._line_count += 1
        if self._line_count > _MAX_VISIBLE_LINES:
            self._textbox.delete("1.0", "2.0")
            self._line_count -= 1
        self._textbox.see("end")
        self._textbox.configure(state="disabled")

    def clear(self) -> None:
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.configure(state="disabled")
        self._line_count = 0
