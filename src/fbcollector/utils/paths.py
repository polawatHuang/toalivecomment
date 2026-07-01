"""Filesystem path resolution for both development and PyInstaller-frozen runs."""

import sys
from pathlib import Path

from fbcollector.constants import APP_DIR_NAME


def is_frozen() -> bool:
    """Return True when running inside a PyInstaller-built executable."""
    return getattr(sys, "frozen", False)


def resolve_repo_root() -> Path:
    """Directory containing ``main.py`` in dev mode, or the executable's folder when frozen."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def resolve_bundle_dir() -> Path:
    """Directory that holds bundled read-only resources (``config``, ``assets``).

    PyInstaller onefile builds extract data files into ``sys._MEIPASS`` at runtime;
    in dev mode this is simply the repo root.
    """
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", resolve_repo_root()))
    return resolve_repo_root()


def resolve_user_data_dir() -> Path:
    """Directory for user-writable runtime state (logs, temp db, default CSV export folder).

    Frozen builds may run from a read-only location (e.g. Program Files), so writable
    state always lives under %LOCALAPPDATA% when frozen, and repo-relative otherwise.
    """
    if is_frozen():
        import os

        local_app_data = os.environ.get("LOCALAPPDATA")
        base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
        return base / APP_DIR_NAME
    return resolve_repo_root()


def logs_dir() -> Path:
    path = resolve_user_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def temp_dir() -> Path:
    path = resolve_user_data_dir() / "temp"
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    """Writable config directory (seeded from the bundled defaults on first run)."""
    if is_frozen():
        path = resolve_user_data_dir() / "config"
        path.mkdir(parents=True, exist_ok=True)
        return path
    path = resolve_repo_root() / "config"
    path.mkdir(parents=True, exist_ok=True)
    return path


def bundled_config_dir() -> Path:
    """Read-only defaults shipped with the app (source of truth for first-run seeding)."""
    return resolve_bundle_dir() / "config"


def assets_dir() -> Path:
    return resolve_bundle_dir() / "assets"


def default_export_dir() -> Path:
    path = resolve_user_data_dir() / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path
