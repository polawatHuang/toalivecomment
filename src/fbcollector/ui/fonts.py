"""Font fallback strategy.

Per the project decision, no custom font files are bundled - the app relies on the
Windows system font stack (Segoe UI, with Tk's own fallback to a default sans-serif if
Segoe UI is somehow unavailable, e.g. on non-Windows dev machines).
"""

import tkinter.font as tkfont

_PREFERRED_FAMILIES = ("Segoe UI", "Segoe UI Variable", "Arial", "Helvetica")


def resolve_available_family() -> str:
    """Return the first preferred family actually installed, else Tk's default."""
    available = set(tkfont.families())
    for family in _PREFERRED_FAMILIES:
        if family in available:
            return family
    return tkfont.nametofont("TkDefaultFont").actual("family")
