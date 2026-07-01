"""Application settings: dataclass model, JSON persistence, migration-safe loading."""

import dataclasses
import json
from dataclasses import dataclass, fields
from pathlib import Path

from fbcollector.constants import DEFAULT_AUTOSAVE_INTERVAL_SECONDS, DEFAULT_EMPLOYEE_ID_REGEX
from fbcollector.utils.paths import config_dir, default_export_dir


@dataclass(slots=True)
class Settings:
    """All user-configurable options, per the spec's Settings screen."""

    employee_id_regex: str = DEFAULT_EMPLOYEE_ID_REGEX
    csv_folder: str = ""
    auto_save_interval_seconds: int = DEFAULT_AUTOSAVE_INTERVAL_SECONDS
    theme: str = "dark"
    language: str = "en"
    animation_speed: str = "normal"  # "slow" | "normal" | "fast"

    def __post_init__(self) -> None:
        if not self.csv_folder:
            self.csv_folder = str(default_export_dir())


class SettingsService:
    """Loads/saves ``Settings`` as JSON. Missing/extra fields never crash loading -
    that's what makes it safe to add new Settings fields across versions."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (config_dir() / "settings.json")

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> Settings:
        if not self._path.exists():
            settings = Settings()
            self.save(settings)
            return settings
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return Settings()
        known_fields = {f.name for f in fields(Settings)}
        filtered = {k: v for k, v in raw.items() if k in known_fields}
        return Settings(**filtered)

    def save(self, settings: Settings) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(dataclasses.asdict(settings), indent=2, ensure_ascii=False), encoding="utf-8"
        )
