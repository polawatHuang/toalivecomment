"""Bottom toolbar: Start, Pause, Stop, Export*, Lucky Wheel, Clear Session."""

from collections.abc import Callable
from dataclasses import dataclass

import customtkinter as ctk

from fbcollector.ui import theme


@dataclass(frozen=True, slots=True)
class ToolbarCallbacks:
    on_start: Callable[[], None]
    on_pause: Callable[[], None]
    on_stop: Callable[[], None]
    on_export_raw: Callable[[], None]
    on_export_users: Callable[[], None]
    on_export_employees: Callable[[], None]
    on_lucky_wheel: Callable[[], None]
    on_clear_session: Callable[[], None]


class BottomToolbar(ctk.CTkFrame):
    """A row of premium pill buttons anchoring the main window."""

    def __init__(self, master, callbacks: ToolbarCallbacks) -> None:
        super().__init__(master, corner_radius=0, fg_color=theme.BG_SURFACE, height=64)

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", padx=16, pady=12)

        self.start_button = self._button(left, "▶ Start", callbacks.on_start, theme.SUCCESS)
        self.pause_button = self._button(left, "⏸ Pause", callbacks.on_pause, theme.WARNING)
        self.stop_button = self._button(left, "⏹ Stop", callbacks.on_stop, theme.DANGER)

        middle = ctk.CTkFrame(self, fg_color="transparent")
        middle.pack(side="left", padx=16, pady=12)
        self._button(middle, "Export Raw CSV", callbacks.on_export_raw)
        self._button(middle, "Export Users CSV", callbacks.on_export_users)
        self._button(middle, "Export Employee CSV", callbacks.on_export_employees)

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=16, pady=12)
        self._button(right, "\U0001f9e7 Clear Session", callbacks.on_clear_session, theme.DANGER, outline=True)
        self._button(right, "\U0001f3a1 Lucky Wheel", callbacks.on_lucky_wheel, theme.ACCENT)

    def _button(
        self,
        parent,
        text: str,
        command: Callable[[], None],
        color: tuple[str, str] | None = None,
        outline: bool = False,
    ) -> ctk.CTkButton:
        kwargs = dict(
            text=text,
            command=command,
            corner_radius=theme.BUTTON_RADIUS,
            font=theme.body_font(12, "bold"),
            height=36,
        )
        if outline:
            kwargs.update(fg_color="transparent", border_width=1, border_color=color, text_color=color)
        elif color is not None:
            kwargs.update(fg_color=color)
        button = ctk.CTkButton(parent, **kwargs)
        button.pack(side="left", padx=4)
        return button

    def set_running_state(self, running: bool) -> None:
        self.start_button.configure(state="disabled" if running else "normal")
        self.pause_button.configure(state="normal" if running else "disabled")
        self.stop_button.configure(state="normal" if running else "disabled")
