"""Settings dialog: General / Collector / Storage / Selectors tabs."""

import json
import re
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from fbcollector.constants import DEFAULT_EMPLOYEE_ID_REGEX
from fbcollector.services.facebook.selectors import (
    SelectorConfigError,
    default_selector_set,
    load_selector_set,
    save_selector_set,
)
from fbcollector.services.settings_service import Settings, SettingsService
from fbcollector.ui import theme


class SettingsDialog(ctk.CTkToplevel):
    """Edits and persists ``Settings`` plus the hot-reloadable selector JSON."""

    def __init__(
        self,
        master,
        settings_service: SettingsService,
        selectors_path: Path,
        on_saved: Callable[[Settings], None],
        on_selectors_reloaded: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self.title("Settings")
        self.geometry("560x480")
        self.configure(fg_color=theme.BG_SURFACE)
        self.transient(master)
        self.grab_set()

        self._settings_service = settings_service
        self._selectors_path = selectors_path
        self._on_saved = on_saved
        self._on_selectors_reloaded = on_selectors_reloaded
        self._settings = settings_service.load()

        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=16, pady=16)
        tabs.add("General")
        tabs.add("Collector")
        tabs.add("Storage")
        tabs.add("Selectors")

        self._build_general_tab(tabs.tab("General"))
        self._build_collector_tab(tabs.tab("Collector"))
        self._build_storage_tab(tabs.tab("Storage"))
        self._build_selectors_tab(tabs.tab("Selectors"))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(footer, text="Cancel", fg_color=theme.BG_CARD_ALT, command=self.destroy).pack(
            side="right", padx=4
        )
        ctk.CTkButton(footer, text="Save", command=self._save).pack(side="right", padx=4)

    def _build_general_tab(self, tab) -> None:
        ctk.CTkLabel(tab, text="Theme").pack(anchor="w", pady=(8, 0))
        self._theme_var = ctk.StringVar(value=self._settings.theme)
        ctk.CTkOptionMenu(tab, values=["dark", "light"], variable=self._theme_var).pack(
            anchor="w", pady=4
        )

        ctk.CTkLabel(tab, text="Language").pack(anchor="w", pady=(12, 0))
        self._language_var = ctk.StringVar(value=self._settings.language)
        ctk.CTkOptionMenu(tab, values=["en", "th"], variable=self._language_var).pack(anchor="w", pady=4)

        ctk.CTkLabel(tab, text="Animation Speed").pack(anchor="w", pady=(12, 0))
        self._animation_var = ctk.StringVar(value=self._settings.animation_speed)
        ctk.CTkOptionMenu(
            tab, values=["slow", "normal", "fast"], variable=self._animation_var
        ).pack(anchor="w", pady=4)

    def _build_collector_tab(self, tab) -> None:
        ctk.CTkLabel(tab, text="Employee ID Regex").pack(anchor="w", pady=(8, 0))
        self._regex_entry = ctk.CTkEntry(tab, width=460)
        self._regex_entry.insert(0, self._settings.employee_id_regex)
        self._regex_entry.pack(anchor="w", pady=4)

        self._regex_test_entry = ctk.CTkEntry(
            tab, width=460, placeholder_text="Test text, e.g. 'Hello my ID is 123456'"
        )
        self._regex_test_entry.pack(anchor="w", pady=(8, 0))
        self._regex_result_label = ctk.CTkLabel(tab, text="", text_color=theme.TEXT_SECONDARY)
        self._regex_result_label.pack(anchor="w", pady=4)
        ctk.CTkButton(tab, text="Test Regex", command=self._test_regex).pack(anchor="w", pady=4)

        ctk.CTkLabel(
            tab,
            text="Poll interval is fixed at 300ms per spec (advanced-only, not user editable).",
            text_color=theme.TEXT_MUTED,
            font=theme.body_font(10),
        ).pack(anchor="w", pady=(16, 0))

    def _build_storage_tab(self, tab) -> None:
        ctk.CTkLabel(tab, text="CSV Export Folder").pack(anchor="w", pady=(8, 0))
        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.pack(anchor="w", fill="x", pady=4)
        self._csv_folder_entry = ctk.CTkEntry(row, width=380)
        self._csv_folder_entry.insert(0, self._settings.csv_folder)
        self._csv_folder_entry.pack(side="left")
        ctk.CTkButton(row, text="Browse...", width=80, command=self._browse_folder).pack(
            side="left", padx=8
        )

        ctk.CTkLabel(tab, text="Auto Save Interval (seconds)").pack(anchor="w", pady=(16, 0))
        self._autosave_entry = ctk.CTkEntry(tab, width=100)
        self._autosave_entry.insert(0, str(self._settings.auto_save_interval_seconds))
        self._autosave_entry.pack(anchor="w", pady=4)

    def _build_selectors_tab(self, tab) -> None:
        ctk.CTkLabel(
            tab,
            text="Facebook's DOM changes without notice - update selectors here if comment "
            "detection stops working.",
            text_color=theme.WARNING,
            font=theme.body_font(11),
            wraplength=480,
            justify="left",
        ).pack(anchor="w", pady=(8, 4))

        self._selectors_text = ctk.CTkTextbox(tab, width=480, height=220, font=theme.mono_font(11))
        self._selectors_text.pack(pady=4)
        self._load_selectors_into_editor()

        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.pack(anchor="w", pady=8)
        ctk.CTkButton(row, text="Reset to Default", command=self._reset_selectors).pack(
            side="left", padx=4
        )
        ctk.CTkButton(row, text="Reload Selectors", command=self._reload_selectors).pack(
            side="left", padx=4
        )

    def _load_selectors_into_editor(self) -> None:
        try:
            selectors = load_selector_set(self._selectors_path)
        except SelectorConfigError:
            selectors = default_selector_set()
        from dataclasses import asdict

        self._selectors_text.delete("1.0", "end")
        self._selectors_text.insert("1.0", json.dumps(asdict(selectors), indent=2, ensure_ascii=False))

    def _reset_selectors(self) -> None:
        save_selector_set(default_selector_set(), self._selectors_path)
        self._load_selectors_into_editor()

    def _reload_selectors(self) -> None:
        try:
            raw = json.loads(self._selectors_text.get("1.0", "end"))
            self._selectors_path.write_text(
                json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            load_selector_set(self._selectors_path)  # validates
        except (json.JSONDecodeError, SelectorConfigError) as exc:
            ctk.CTkLabel(self, text=f"Invalid selector JSON: {exc}", text_color=theme.DANGER).pack()
            return
        self._on_selectors_reloaded()

    def _test_regex(self) -> None:
        try:
            pattern = re.compile(self._regex_entry.get())
        except re.error as exc:
            self._regex_result_label.configure(text=f"Invalid regex: {exc}", text_color=theme.DANGER)
            return
        match = pattern.search(self._regex_test_entry.get())
        if match:
            self._regex_result_label.configure(
                text=f"Match: {match.group(0)}", text_color=theme.SUCCESS
            )
        else:
            self._regex_result_label.configure(text="No match", text_color=theme.TEXT_MUTED)

    def _browse_folder(self) -> None:
        folder = filedialog.askdirectory(initialdir=self._csv_folder_entry.get() or None)
        if folder:
            self._csv_folder_entry.delete(0, "end")
            self._csv_folder_entry.insert(0, folder)

    def _save(self) -> None:
        try:
            interval = int(self._autosave_entry.get())
        except ValueError:
            interval = self._settings.auto_save_interval_seconds

        regex_value = self._regex_entry.get().strip() or DEFAULT_EMPLOYEE_ID_REGEX
        try:
            re.compile(regex_value)
        except re.error:
            regex_value = self._settings.employee_id_regex

        updated = Settings(
            employee_id_regex=regex_value,
            csv_folder=self._csv_folder_entry.get().strip() or self._settings.csv_folder,
            auto_save_interval_seconds=max(1, interval),
            theme=self._theme_var.get(),
            language=self._language_var.get(),
            animation_speed=self._animation_var.get(),
        )
        self._settings_service.save(updated)
        self._on_saved(updated)
        self.destroy()
