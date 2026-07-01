"""Wheel entrant/winner state, CSV import, and the background WheelWorker thread.

Canvas animation itself must run on the Tk thread (Tkinter is not thread-safe), so the
*data* side of the Lucky Wheel - CSV import parsing and winner-history persistence -
runs on a dedicated background thread instead, communicating via
``queue_bus.wheel_commands`` in and ``WheelResultEvent``/``LogEvent`` out.
"""

import csv
import queue
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from fbcollector.core.events import LogEvent, UIEvent, WheelCommand, WheelResultEvent
from fbcollector.services.storage.models import Winner
from fbcollector.services.storage.repositories import WinnerRepository


@dataclass(frozen=True, slots=True)
class WheelEntrant:
    name: str
    employee_id: str | None = None


class WheelSession:
    """Holds entrants, winner history, and the remove-after-draw toggle for one wheel run."""

    def __init__(self) -> None:
        self.entrants: list[WheelEntrant] = []
        self.remove_winner_after_draw: bool = True

    def load_entrants_from_csv(
        self, path: Path, source: Literal["unique_users", "employee_ids"]
    ) -> None:
        entrants: list[WheelEntrant] = []
        with open(path, newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if source == "unique_users":
                    entrants.append(WheelEntrant(name=row.get("Username", "").strip()))
                else:
                    entrants.append(
                        WheelEntrant(
                            name=row.get("First User", "").strip(),
                            employee_id=row.get("EmployeeID", "").strip(),
                        )
                    )
        self.entrants = [e for e in entrants if e.name]

    def record_winner(self, winner: WheelEntrant, prize: str) -> Winner:
        result = Winner(
            winner_name=winner.name, employee_id=winner.employee_id, prize=prize, drawn_at=datetime.now()
        )
        if self.remove_winner_after_draw:
            self.remove_from_pool(winner)
        return result

    def remove_from_pool(self, entrant: WheelEntrant) -> None:
        self.entrants = [e for e in self.entrants if e != entrant]


class WheelWorker(threading.Thread):
    """Background thread handling CSV import and winner persistence off the Tk thread.

    Takes its own dedicated command/event queues (not the app-wide ``QueueBus.ui_events``)
    so its results can be polled independently by ``WheelWindow`` without racing
    ``MainWindow``'s drain of the shared event queue.
    """

    def __init__(
        self,
        commands: "queue.Queue[WheelCommand]",
        events: "queue.Queue[UIEvent]",
        winner_repo: WinnerRepository,
        session: WheelSession,
    ) -> None:
        super().__init__(name="WheelWorker", daemon=True)
        self._commands = commands
        self._events = events
        self._winner_repo = winner_repo
        self._session = session
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                command: WheelCommand = self._commands.get(timeout=0.25)
            except queue.Empty:
                continue
            self._handle(command)

    def _handle(self, command: WheelCommand) -> None:
        if command.kind == "import_csv":
            path, source = command.payload
            try:
                self._session.load_entrants_from_csv(Path(path), source)
                self._events.put_nowait(
                    LogEvent(level="INFO", message=f"Loaded {len(self._session.entrants)} entrants from {path}")
                )
            except OSError as exc:
                self._events.put_nowait(LogEvent(level="ERROR", message=f"CSV import failed: {exc}"))
        elif command.kind == "record_winner":
            entrant, prize = command.payload
            winner = self._session.record_winner(entrant, prize)
            self._winner_repo.add(winner)
            self._events.put_nowait(WheelResultEvent(winner=winner))
