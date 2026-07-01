"""Full-screen Lucky Wheel modal: canvas wheel, spin animation, winner panel, history."""

import math
import queue
import time
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from fbcollector.core.events import LogEvent, UIEvent, WheelCommand, WheelResultEvent
from fbcollector.constants import WHEEL_FRAME_INTERVAL_MS
from fbcollector.services.export.csv_writer import CsvWriterService
from fbcollector.services.storage.repositories import RepoBundle
from fbcollector.services.wheel.confetti import ParticleSystem
from fbcollector.services.wheel.wheel_engine import WheelPhysics, WheelSpinPlan
from fbcollector.services.wheel.wheel_state import WheelEntrant, WheelSession, WheelWorker
from fbcollector.ui import theme

_WHEEL_COLORS = ("#6C5CE7", "#00d2ff", "#f5b942", "#ff5c5c", "#2ecc71", "#ff8fd6", "#54a0ff", "#feca57")


class WheelWindow(ctk.CTkToplevel):
    """Standalone full-screen prize-draw window."""

    def __init__(self, master, repos: RepoBundle, csv_writer: CsvWriterService) -> None:
        super().__init__(master)
        self.title("Lucky Wheel")
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        self.configure(fg_color=theme.BG_ROOT)
        self.transient(master)

        self._repos = repos
        self._csv_writer = csv_writer
        self._session = WheelSession()
        self._particles = ParticleSystem()

        self._commands: "queue.Queue[WheelCommand]" = queue.Queue()
        self._events: "queue.Queue[UIEvent]" = queue.Queue()
        self._worker = WheelWorker(self._commands, self._events, repos.winners, self._session)
        self._worker.start()

        self._spinning = False
        self._current_plan: WheelSpinPlan | None = None
        self._spin_start_time: float = 0.0

        self._build_layout()
        self._poll_worker_events()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # --- layout ------------------------------------------------------------------

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)

        self._canvas = tk.Canvas(left, bg=self._tk_bg(), highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)

        controls = ctk.CTkFrame(left, fg_color="transparent")
        controls.pack(fill="x", pady=8)
        ctk.CTkButton(controls, text="\U0001f3af SPIN", command=self._on_spin, height=44,
                      font=theme.heading_font(16), fg_color=theme.ACCENT).pack(side="left", padx=4)
        ctk.CTkButton(controls, text="Close", command=self._on_close, fg_color=theme.BG_CARD_ALT).pack(
            side="right", padx=4
        )

        right = ctk.CTkFrame(self, fg_color=theme.BG_SURFACE, corner_radius=theme.CARD_RADIUS)
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)

        ctk.CTkLabel(right, text="Entrants", font=theme.heading_font(14)).pack(anchor="w", padx=12, pady=(12, 4))
        row = ctk.CTkFrame(right, fg_color="transparent")
        row.pack(fill="x", padx=12)
        ctk.CTkButton(row, text="Import UniqueUsers.csv", command=lambda: self._import_csv("unique_users")).pack(
            fill="x", pady=2
        )
        ctk.CTkButton(row, text="Import EmployeeIDs.csv", command=lambda: self._import_csv("employee_ids")).pack(
            fill="x", pady=2
        )
        self._entrant_count_label = ctk.CTkLabel(right, text="0 entrants loaded", text_color=theme.TEXT_SECONDARY)
        self._entrant_count_label.pack(anchor="w", padx=12, pady=4)

        self._remove_winner_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            right, text="Remove winner after draw", variable=self._remove_winner_var,
            command=self._on_toggle_remove
        ).pack(anchor="w", padx=12, pady=8)

        ctk.CTkLabel(right, text="Prize").pack(anchor="w", padx=12, pady=(8, 0))
        self._prize_entry = ctk.CTkEntry(right, placeholder_text="e.g. Gift Voucher")
        self._prize_entry.pack(fill="x", padx=12, pady=4)

        self._winner_panel = ctk.CTkFrame(right, fg_color=theme.BG_CARD, corner_radius=theme.CARD_RADIUS)
        self._winner_panel.pack(fill="x", padx=12, pady=12)
        self._winner_name_label = ctk.CTkLabel(self._winner_panel, text="No winner yet", font=theme.heading_font(15))
        self._winner_name_label.pack(padx=10, pady=(10, 2))
        self._winner_detail_label = ctk.CTkLabel(self._winner_panel, text="", text_color=theme.TEXT_SECONDARY)
        self._winner_detail_label.pack(padx=10, pady=(0, 10))

        ctk.CTkLabel(right, text="Winner History", font=theme.heading_font(14)).pack(
            anchor="w", padx=12, pady=(12, 4)
        )
        self._history_box = ctk.CTkTextbox(right, height=180, font=theme.mono_font(11))
        self._history_box.pack(fill="both", expand=True, padx=12, pady=4)
        self._history_box.configure(state="disabled")

        ctk.CTkButton(right, text="Export Winner History CSV", command=self._export_history).pack(
            fill="x", padx=12, pady=12
        )

        self._draw_wheel(0.0)
        self._refresh_history()

    def _tk_bg(self) -> str:
        mode = ctk.get_appearance_mode()
        return theme.BG_ROOT[0] if mode == "Dark" else theme.BG_ROOT[1]

    # --- CSV import ------------------------------------------------------------------

    def _import_csv(self, source: str) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        self._commands.put_nowait(WheelCommand(kind="import_csv", payload=(path, source)))

    def _on_toggle_remove(self) -> None:
        self._session.remove_winner_after_draw = self._remove_winner_var.get()

    # --- spin --------------------------------------------------------------------

    def _on_spin(self) -> None:
        if self._spinning or not self._session.entrants:
            return
        self._spinning = True
        plan = WheelPhysics.plan_spin(len(self._session.entrants))
        self._current_plan = plan
        self._spin_start_time = time.monotonic()
        self._animate_spin()

    def _animate_spin(self) -> None:
        plan = self._current_plan
        if plan is None:
            return
        elapsed_ms = int((time.monotonic() - self._spin_start_time) * 1000)
        angle = WheelPhysics.angle_at(elapsed_ms, plan)
        self._draw_wheel(angle)
        if elapsed_ms < plan.duration_ms:
            self.after(WHEEL_FRAME_INTERVAL_MS, self._animate_spin)
        else:
            self._on_spin_complete(plan.winner_index)

    def _on_spin_complete(self, winner_index: int) -> None:
        self._spinning = False
        winner = self._session.entrants[winner_index]
        prize = self._prize_entry.get().strip() or "Prize"
        self._commands.put_nowait(WheelCommand(kind="record_winner", payload=(winner, prize)))
        center = (self._canvas.winfo_width() / 2, self._canvas.winfo_height() / 2)
        self._particles.spawn_burst(center, count=100)
        self._animate_particles()

    def _animate_particles(self) -> None:
        self._particles.step(WHEEL_FRAME_INTERVAL_MS / 1000)
        self._draw_wheel(self._current_wheel_angle())
        if self._particles.particles:
            self.after(WHEEL_FRAME_INTERVAL_MS, self._animate_particles)

    def _current_wheel_angle(self) -> float:
        if self._current_plan is None:
            return 0.0
        return self._current_plan.total_rotation_degrees % 360.0

    # --- rendering ----------------------------------------------------------------

    def _draw_wheel(self, rotation_degrees: float) -> None:
        self._canvas.delete("all")
        width = max(self._canvas.winfo_width(), 400)
        height = max(self._canvas.winfo_height(), 400)
        cx, cy = width / 2, height / 2
        radius = min(width, height) / 2 - 30

        entrants = self._session.entrants or [WheelEntrant(name="No entrants loaded")]
        segment_degrees = 360.0 / len(entrants)

        for i, entrant in enumerate(entrants):
            start_angle = rotation_degrees + i * segment_degrees
            color = _WHEEL_COLORS[i % len(_WHEEL_COLORS)]
            self._canvas.create_arc(
                cx - radius, cy - radius, cx + radius, cy + radius,
                start=start_angle, extent=segment_degrees, fill=color, outline=self._tk_bg(), width=2,
            )
            label_angle = math.radians(start_angle + segment_degrees / 2)
            label_x = cx + (radius * 0.65) * math.cos(label_angle)
            label_y = cy - (radius * 0.65) * math.sin(label_angle)
            self._canvas.create_text(
                label_x, label_y, text=entrant.name[:14], fill="white", font=(theme.FONT_FAMILY, 11, "bold")
            )

        # pointer at the top
        self._canvas.create_polygon(
            cx - 12, cy - radius - 6, cx + 12, cy - radius - 6, cx, cy - radius + 18,
            fill=theme.DANGER[0],
        )

        for particle in self._particles.particles:
            self._canvas.create_oval(
                particle.x - particle.size, particle.y - particle.size,
                particle.x + particle.size, particle.y + particle.size,
                fill=particle.color, outline="",
            )

    # --- worker event polling -----------------------------------------------------

    def _poll_worker_events(self) -> None:
        try:
            while True:
                event = self._events.get_nowait()
                self._dispatch(event)
        except queue.Empty:
            pass
        self.after(100, self._poll_worker_events)

    def _dispatch(self, event) -> None:
        if isinstance(event, WheelResultEvent):
            self._winner_name_label.configure(text=f"\U0001f3c6 {event.winner.winner_name}")
            detail = f"ID: {event.winner.employee_id or '-'}  ·  Prize: {event.winner.prize}"
            self._winner_detail_label.configure(text=detail)
            self._refresh_history()
        elif isinstance(event, LogEvent) and event.level == "INFO":
            self._entrant_count_label.configure(text=f"{len(self._session.entrants)} entrants loaded")
            self._draw_wheel(0.0)

    def _refresh_history(self) -> None:
        self._history_box.configure(state="normal")
        self._history_box.delete("1.0", "end")
        for winner in self._repos.winners.all():
            self._history_box.insert(
                "end", f"{winner.drawn_at:%H:%M:%S}  {winner.winner_name:<20}  {winner.prize}\n"
            )
        self._history_box.configure(state="disabled")

    def _export_history(self) -> None:
        self._csv_writer.write_winner_history()

    def _on_close(self) -> None:
        self._worker.stop()
        self.destroy()
