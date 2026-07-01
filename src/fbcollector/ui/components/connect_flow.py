"""Modal shown while CONNECT is running: step indicator + cancel."""

from collections.abc import Callable

import customtkinter as ctk

from fbcollector.core.events import ConnectionStatusEvent
from fbcollector.ui import theme


class ConnectDialog(ctk.CTkToplevel):
    """Non-blocking progress modal for the CONNECT sequence.

    The actual connect work (launching Chrome, CDP attach, waiting for a Facebook page)
    runs on a background thread; this dialog only reflects the ``ConnectionStatusEvent``
    stream and lets the user cancel.
    """

    def __init__(self, master, on_cancel: Callable[[], None]) -> None:
        super().__init__(master)
        self.title("Connecting")
        self.geometry("420x220")
        self.resizable(False, False)
        self.configure(fg_color=theme.BG_SURFACE)
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text="Connecting to Facebook Live", font=theme.heading_font(16)).pack(
            pady=(24, 8)
        )
        self._step_label = ctk.CTkLabel(
            self, text="Launching Chrome...", font=theme.body_font(13), text_color=theme.TEXT_SECONDARY
        )
        self._step_label.pack(pady=4)

        self._progress = ctk.CTkProgressBar(self, mode="indeterminate", width=320)
        self._progress.pack(pady=16)
        self._progress.start()

        ctk.CTkLabel(
            self,
            text=(
                "A new Chrome window has opened.\n"
                "Please open your Facebook Live video there and keep the window open."
            ),
            font=theme.body_font(11),
            text_color=theme.TEXT_MUTED,
            justify="center",
        ).pack(pady=4)

        ctk.CTkButton(
            self, text="Cancel", fg_color=theme.DANGER, command=lambda: self._cancel(on_cancel)
        ).pack(pady=12)

    def _cancel(self, on_cancel: Callable[[], None]) -> None:
        on_cancel()
        self.destroy()

    def update_status(self, event: ConnectionStatusEvent) -> None:
        self._step_label.configure(text=event.message)
        if event.chrome_connected and event.facebook_detected:
            self._progress.stop()
            self._progress.set(1.0)
            self.after(800, self.destroy)
