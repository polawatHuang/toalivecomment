"""Color tokens and palette definitions for the premium dark/light dashboard look."""

import customtkinter as ctk

# (dark, light) tuples, per CustomTkinter's convention
ACCENT = ("#6C5CE7", "#6C5CE7")
ACCENT_HOVER = ("#5b4bd6", "#7d6ef0")
SUCCESS = ("#2ecc71", "#27ae60")
DANGER = ("#ff5c5c", "#e74c3c")
WARNING = ("#f5b942", "#f39c12")

BG_ROOT = ("#0f1117", "#f4f5f9")
BG_SURFACE = ("#171a23", "#ffffff")
BG_CARD = ("#1c2030", "#ffffff")
BG_CARD_ALT = ("#232839", "#f0f1f7")

BORDER_SUBTLE = ("#2a2f42", "#e2e4ee")

TEXT_PRIMARY = ("#f5f6fa", "#161822")
TEXT_SECONDARY = ("#9aa0b4", "#666b80")
TEXT_MUTED = ("#5c6178", "#9298ac")

CARD_RADIUS = 16
BUTTON_RADIUS = 12
PILL_RADIUS = 20

FONT_FAMILY = "Segoe UI"


def apply_appearance(mode: str) -> None:
    """mode: 'dark' | 'light' | 'system'."""
    ctk.set_appearance_mode(mode)


def configure_default_theme() -> None:
    ctk.set_default_color_theme("dark-blue")


def heading_font(size: int = 20, weight: str = "bold") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def body_font(size: int = 13, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def mono_font(size: int = 12) -> ctk.CTkFont:
    return ctk.CTkFont(family="Consolas", size=size)


_ANIMATION_SPEED_MS = {"slow": 30, "normal": 16, "fast": 8}


def animation_tick_ms(speed: str) -> int:
    return _ANIMATION_SPEED_MS.get(speed, 16)
