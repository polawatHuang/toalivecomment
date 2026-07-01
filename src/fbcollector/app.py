"""Application bootstrap: builds all services, wires the QueueBus, and starts the UI."""

import shutil
from pathlib import Path

import customtkinter as ctk

from fbcollector.constants import DB_FILENAME
from fbcollector.core.queues import QueueBus
from fbcollector.core.session import SessionController
from fbcollector.services.export.csv_writer import CsvWriterService
from fbcollector.services.facebook.selectors import SelectorConfigError, load_selector_set
from fbcollector.services.settings_service import SettingsService
from fbcollector.services.storage.db import SQLiteConnectionManager
from fbcollector.services.storage.repositories import RepoBundle
from fbcollector.ui import theme
from fbcollector.ui.main_window import MainWindow
from fbcollector.utils.logger import setup_logging
from fbcollector.utils.paths import bundled_config_dir, config_dir, temp_dir


def _seed_config_files() -> tuple[Path, Path]:
    """Copy bundled default config files into the writable config dir on first run."""
    target_dir = config_dir()
    source_dir = bundled_config_dir()

    settings_path = target_dir / "settings.json"
    if not settings_path.exists():
        default_settings = source_dir / "settings.default.json"
        if default_settings.exists():
            shutil.copy(default_settings, settings_path)

    selectors_path = target_dir / "selectors.json"
    if not selectors_path.exists():
        default_selectors = source_dir / "selectors.default.json"
        if default_selectors.exists():
            shutil.copy(default_selectors, selectors_path)

    return settings_path, selectors_path


def main() -> None:
    setup_logging()

    settings_path, selectors_path = _seed_config_files()
    settings_service = SettingsService(settings_path)
    settings = settings_service.load()

    try:
        selectors = load_selector_set(selectors_path)
    except SelectorConfigError:
        from fbcollector.services.facebook.selectors import default_selector_set

        selectors = default_selector_set()

    db = SQLiteConnectionManager(temp_dir() / DB_FILENAME)
    db.initialize_schema()
    repos = RepoBundle(db)

    csv_writer = CsvWriterService(
        repos, output_dir=Path(settings.csv_folder), interval_seconds=settings.auto_save_interval_seconds
    )

    queue_bus = QueueBus()
    session = SessionController(queue_bus, db, repos, csv_writer, settings_service, selectors)

    theme.configure_default_theme()
    theme.apply_appearance(settings.theme)
    ctk.set_widget_scaling(1.0)

    window = MainWindow(queue_bus, session, settings_service, selectors_path, repos, csv_writer)
    window.mainloop()


if __name__ == "__main__":
    main()
