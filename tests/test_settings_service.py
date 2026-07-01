import json

from fbcollector.services.settings_service import Settings, SettingsService


def test_load_creates_defaults_when_missing(tmp_path):
    service = SettingsService(tmp_path / "settings.json")
    settings = service.load()

    assert settings.employee_id_regex == Settings().employee_id_regex
    assert (tmp_path / "settings.json").exists()


def test_save_and_reload_round_trip(tmp_path):
    service = SettingsService(tmp_path / "settings.json")
    settings = Settings(employee_id_regex=r"\d{6}", theme="light", auto_save_interval_seconds=10)
    service.save(settings)

    reloaded = service.load()
    assert reloaded.employee_id_regex == r"\d{6}"
    assert reloaded.theme == "light"
    assert reloaded.auto_save_interval_seconds == 10


def test_load_ignores_unknown_fields_gracefully(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"theme": "dark", "some_future_field": "unexpected"}), encoding="utf-8"
    )
    service = SettingsService(path)
    settings = service.load()
    assert settings.theme == "dark"


def test_load_falls_back_to_defaults_on_missing_fields(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"theme": "light"}), encoding="utf-8")
    service = SettingsService(path)
    settings = service.load()
    assert settings.theme == "light"
    assert settings.auto_save_interval_seconds == Settings().auto_save_interval_seconds


def test_load_falls_back_to_defaults_on_corrupt_json(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")
    service = SettingsService(path)
    settings = service.load()
    assert settings == Settings(csv_folder=settings.csv_folder)
