import json

import pytest

from fbcollector.services.facebook.selectors import (
    SelectorConfigError,
    default_selector_set,
    load_selector_set,
    save_selector_set,
)


def test_round_trip_default_selector_set(tmp_path):
    path = tmp_path / "selectors.json"
    original = default_selector_set()
    save_selector_set(original, path)

    loaded = load_selector_set(path)
    assert loaded.comment_container == original.comment_container
    assert loaded.username_selectors == original.username_selectors
    assert loaded.text_selectors == original.text_selectors
    assert loaded.aria_label_pattern == original.aria_label_pattern


def test_missing_file_raises_typed_error(tmp_path):
    with pytest.raises(SelectorConfigError):
        load_selector_set(tmp_path / "does_not_exist.json")


def test_malformed_json_raises_typed_error(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(SelectorConfigError):
        load_selector_set(path)


def test_missing_required_field_raises_typed_error(tmp_path):
    path = tmp_path / "incomplete.json"
    path.write_text(json.dumps({"comment_container": "[role=article]"}), encoding="utf-8")
    with pytest.raises(SelectorConfigError):
        load_selector_set(path)
