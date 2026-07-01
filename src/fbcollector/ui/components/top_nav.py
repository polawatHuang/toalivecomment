"""Top navigation bar: logo, app name, connection status pill, theme switch, settings gear."""

from collections.abc import Callable

import customtkinter as ctk

from fbcollector.constants import APP_EDITION, APP_NAME
from fbcollector.core.events import ConnectionStatusEvent
from fbcollector.ui import theme


class ConnectionStatusPill(ctk.CTkFrame):
    """Colored dot + text summarizing Chrome/Facebook connection state."""

    def __init__(self, master) -> None:
        super().__init__(master, corner_radius=theme.PILL_RADIUS, fg_color=theme.BG_CARD_ALT)
        self._dot = ctk.CTkLabel(self, text="●", text_color=theme.DANGER, font=theme.body_font(14))
        self._dot.pack(side="left", padx=(12, 4), pady=6)
        self._label = ctk.CTkLabel(self, text="Disconnected", font=theme.body_font(12))
        self._label.pack(side="left", padx=(0, 12), pady=6)

    def update_status(self, event: ConnectionStatusEvent) -> None:
        if event.chrome_connected and event.facebook_detected:
            color = theme.SUCCESS
        elif event.chrome_connected:
            color = theme.WARNING
        else:
            color = theme.DANGER
        self._dot.configure(text_color=color)
        self._label.configure(text=event.message)


class TopNavBar(ctk.CTkFrame):
    """Logo, app name/edition, connection status, theme toggle, settings gear."""

    def __init__(
        self,
        master,
        on_toggle_theme: Callable[[bool], None],
        on_open_settings: Callable[[], None],
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=theme.BG_SURFACE, height=64)
        self.grid_columnconfigure(1, weight=1)

        brand_frame = ctk.CTkFrame(self, fg_color="transparent")
        brand_frame.grid(row=0, column=0, sticky="w", padx=16, pady=10)
        ctk.CTkLabel(
            brand_frame, text="\U0001f4e1", font=theme.heading_font(22), text_color=theme.ACCENT
        ).pack(side="left", padx=(0, 8))
        name_frame = ctk.CTkFrame(brand_frame, fg_color="transparent")
        name_frame.pack(side="left")
        ctk.CTkLabel(name_frame, text=APP_NAME, font=theme.heading_font(16), anchor="w").pack(
            anchor="w"
        )
        ctk.CTkLabel(
            name_frame,
            text=APP_EDITION,
            font=theme.body_font(10),
            text_color=theme.TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w")

        self.status_pill = ConnectionStatusPill(self)
        self.status_pill.grid(row=0, column=1, sticky="e", padx=8)

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=0, column=2, sticky="e", padx=16)

        self._theme_switch = ctk.CTkSwitch(
            controls, text="Dark Mode", command=lambda: on_toggle_theme(self._theme_switch.get() == 1)
        )
        self._theme_switch.select()
        self._theme_switch.pack(side="left", padx=8)

        ctk.CTkButton(
            controls,
            text="⚙",
            width=36,
            height=32,
            corner_radius=theme.BUTTON_RADIUS,
            fg_color=theme.BG_CARD_ALT,
            hover_color=theme.ACCENT_HOVER,
            command=on_open_settings,
        ).pack(side="left", padx=8)
