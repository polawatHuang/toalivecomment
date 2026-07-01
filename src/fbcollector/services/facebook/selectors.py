"""Configurable DOM selector set used to locate comments on a Facebook Live page.

Facebook's DOM is obfuscated and changes frequently; hardcoding class names here would
be brittle and unverifiable in this environment. Instead, the selector set is externally
configurable JSON (``config/selectors.json``), hot-reloadable from Settings, so operators
can adapt to DOM drift without a code change or app restart.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


class SelectorConfigError(ValueError):
    """Raised when a selector JSON file is missing required fields or malformed."""


@dataclass(frozen=True, slots=True)
class SelectorSet:
    """BEST-EFFORT, unverified against live Facebook DOM. Update via config/selectors.json
    if comment detection stops working - Facebook changes its markup without notice."""

    comment_container: str = '[role="article"]'
    username_selectors: list[str] = field(
        default_factory=lambda: ['[aria-label] a[role="link"]', "h3 a", "h4 a", "span a"]
    )
    text_selectors: list[str] = field(
        default_factory=lambda: ['[data-ad-preview="message"]', "div[dir='auto']", "span[dir='auto']"]
    )
    aria_label_pattern: str = r"^(?P<username>.+?) commented[: ]+(?P<comment>.*)$"
    version: str = "1.0-best-effort"
    notes: str = (
        "Unverified against live Facebook DOM (no live page available at authoring time). "
        "role=article is Facebook's long-standing semantic wrapper for feed/comment items; "
        "the username/text selectors are an ordered fallback chain tried in turn. If comment "
        "detection stops working, inspect the live page's DOM (F12) and update this file or the "
        "Selectors tab in Settings - no app restart required, use 'Reload Selectors'."
    )


def load_selector_set(path: Path) -> SelectorSet:
    if not path.exists():
        raise SelectorConfigError(f"Selector config not found: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SelectorConfigError(f"Malformed selector JSON at {path}: {exc}") from exc

    required = {"comment_container", "username_selectors", "text_selectors", "aria_label_pattern"}
    missing = required - raw.keys()
    if missing:
        raise SelectorConfigError(f"Selector config {path} missing required fields: {sorted(missing)}")

    return SelectorSet(
        comment_container=raw["comment_container"],
        username_selectors=list(raw["username_selectors"]),
        text_selectors=list(raw["text_selectors"]),
        aria_label_pattern=raw["aria_label_pattern"],
        version=raw.get("version", "unknown"),
        notes=raw.get("notes", ""),
    )


def save_selector_set(selectors: SelectorSet, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(selectors), indent=2, ensure_ascii=False), encoding="utf-8")


def default_selector_set() -> SelectorSet:
    return SelectorSet()
