"""CSV export with autosave, dirty-flag change tracking, and atomic writes.

Writes UTF-8 with a BOM (``utf-8-sig``) so Excel opens the files without mojibake.
Each write goes to a temp file first and is then atomically ``os.replace``d over the
target so a reader (e.g. Excel with the file open) never observes a half-written file,
and a crash mid-write can't corrupt the previous good export.
"""

import csv
import os
import threading
from pathlib import Path

from fbcollector.constants import (
    EMPLOYEE_IDS_FILENAME,
    RAW_COMMENTS_FILENAME,
    UNIQUE_USERS_FILENAME,
    WINNER_HISTORY_FILENAME,
)
from fbcollector.services.storage.repositories import RepoBundle
from fbcollector.utils.logger import get_logger

_log = get_logger("csv_writer")


class CsvWriterService:
    """Auto-saves every N seconds using a dirty-flag + timer, and supports on-demand export."""

    def __init__(self, repos: RepoBundle, output_dir: Path, interval_seconds: int = 5) -> None:
        self._repos = repos
        self._output_dir = output_dir
        self._interval_seconds = interval_seconds
        self._dirty = threading.Event()
        self._timer: threading.Timer | None = None

    @property
    def output_dir(self) -> Path:
        return self._output_dir

    def set_output_dir(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def mark_dirty(self) -> None:
        self._dirty.set()

    def start_autosave_loop(self, stop_event: threading.Event) -> None:
        """Blocking loop intended to run on its own thread (or be driven by WriterThread)."""
        while not stop_event.is_set():
            if stop_event.wait(self._interval_seconds):
                break
            if self._dirty.is_set():
                self._dirty.clear()
                try:
                    self.write_raw_comments()
                    self.write_unique_users()
                    self.write_employee_ids()
                except OSError as exc:
                    _log.error("Autosave failed: %s", exc)

    def _atomic_write_rows(self, filename: str, headers: list[str], rows: list[list[str]]) -> Path:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        target = self._output_dir / filename
        tmp_path = self._output_dir / f".{filename}.tmp"
        with open(tmp_path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(rows)
        os.replace(tmp_path, target)
        return target

    def write_raw_comments(self) -> Path:
        comments = self._repos.comments.fetch_page(0, self._repos.comments.count())
        comments.reverse()  # fetch_page returns newest-first; CSV reads naturally oldest-first
        from fbcollector.services.storage.models import RawComment

        path = self._atomic_write_rows(
            RAW_COMMENTS_FILENAME, RawComment.csv_headers(), [c.to_csv_row() for c in comments]
        )
        _log.info("CSV saved: %s (%d rows)", path, len(comments))
        return path

    def write_unique_users(self) -> Path:
        from fbcollector.services.storage.models import UniqueUser

        users = self._repos.users.all()
        path = self._atomic_write_rows(
            UNIQUE_USERS_FILENAME, UniqueUser.csv_headers(), [u.to_csv_row() for u in users]
        )
        _log.info("CSV saved: %s (%d rows)", path, len(users))
        return path

    def write_employee_ids(self) -> Path:
        from fbcollector.services.storage.models import EmployeeIdEntry

        entries = self._repos.employees.all()
        path = self._atomic_write_rows(
            EMPLOYEE_IDS_FILENAME, EmployeeIdEntry.csv_headers(), [e.to_csv_row() for e in entries]
        )
        _log.info("CSV saved: %s (%d rows)", path, len(entries))
        return path

    def write_winner_history(self) -> Path:
        from fbcollector.services.storage.models import Winner

        winners = self._repos.winners.all()
        path = self._atomic_write_rows(
            WINNER_HISTORY_FILENAME, Winner.csv_headers(), [w.to_csv_row() for w in winners]
        )
        _log.info("Export finished: %s (%d rows)", path, len(winners))
        return path
