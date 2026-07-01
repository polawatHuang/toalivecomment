"""Dashboard stat cards: Chrome status, Facebook status, running time, counts, memory."""

import customtkinter as ctk

from fbcollector.core.events import ConnectionStatusEvent, StatsEvent
from fbcollector.ui import theme
from fbcollector.utils.perf import format_running_time


class StatCard(ctk.CTkFrame):
    """A single rounded, softly-elevated stat tile with a title and a big value."""

    def __init__(self, master, title: str, icon: str = "") -> None:
        super().__init__(master, corner_radius=theme.CARD_RADIUS, fg_color=theme.BG_CARD)
        self.grid_propagate(False)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(header, text=icon, font=theme.body_font(14)).pack(side="left")
        ctk.CTkLabel(
            header, text=title, font=theme.body_font(11), text_color=theme.TEXT_SECONDARY
        ).pack(side="left", padx=(6, 0))

        self._value_label = ctk.CTkLabel(self, text="-", font=theme.heading_font(22), anchor="w")
        self._value_label.pack(fill="x", padx=14, pady=(4, 12))

    def set_value(self, value: str) -> None:
        self._value_label.configure(text=value)


class DashboardPanel(ctk.CTkFrame):
    """Horizontal row of StatCards, updated from StatsEvent/ConnectionStatusEvent."""

    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")
        for i in range(7):
            self.grid_columnconfigure(i, weight=1, uniform="cards")

        self.card_chrome = StatCard(self, "Chrome Status", "\U0001f310")
        self.card_facebook = StatCard(self, "Facebook Status", "\U0001f4d8")
        self.card_running_time = StatCard(self, "Running Time", "⏱")
        self.card_total_comments = StatCard(self, "Total Comments", "\U0001f4ac")
        self.card_unique_users = StatCard(self, "Unique Users", "\U0001f465")
        self.card_employee_ids = StatCard(self, "Employee IDs", "\U0001f194")
        self.card_memory = StatCard(self, "Memory Usage", "\U0001f4be")

        for i, card in enumerate(
            (
                self.card_chrome,
                self.card_facebook,
                self.card_running_time,
                self.card_total_comments,
                self.card_unique_users,
                self.card_employee_ids,
                self.card_memory,
            )
        ):
            card.grid(row=0, column=i, sticky="nsew", padx=6, pady=6)
            card.configure(height=90)

        self.card_chrome.set_value("Offline")
        self.card_facebook.set_value("Not Detected")
        self.card_running_time.set_value("00:00:00")
        self.card_total_comments.set_value("0")
        self.card_unique_users.set_value("0")
        self.card_employee_ids.set_value("0")
        self.card_memory.set_value("0 MB")

    def update_connection(self, event: ConnectionStatusEvent) -> None:
        self.card_chrome.set_value("Online" if event.chrome_connected else "Offline")
        self.card_facebook.set_value("Detected" if event.facebook_detected else "Not Detected")

    def update_stats(self, event: StatsEvent) -> None:
        self.card_running_time.set_value(format_running_time(event.running_seconds))
        self.card_total_comments.set_value(f"{event.total_comments:,}")
        self.card_unique_users.set_value(f"{event.unique_users:,}")
        self.card_employee_ids.set_value(f"{event.employee_ids:,}")
        self.card_memory.set_value(f"{event.memory_mb:.0f} MB")

    def reset(self) -> None:
        self.card_running_time.set_value("00:00:00")
        self.card_total_comments.set_value("0")
        self.card_unique_users.set_value("0")
        self.card_employee_ids.set_value("0")
