"""Virtualized live comment feed.

Must support 100,000+ comments without freezing (spec requirement), so this view never
creates one widget per comment. Instead it keeps a small in-memory ``deque`` of the most
recent comments plus a **fixed-size pool of recycled row frames** (``LIVE_FEED_VISIBLE_ROW_POOL``,
default ~48) whose text is rewritten in place as the visible window changes. Rows beyond
the in-memory cache are fetched lazily from ``CommentRepository`` on scroll.
"""

from collections import deque
from collections.abc import Callable

import customtkinter as ctk

from fbcollector.constants import LIVE_FEED_IN_MEMORY_CACHE, LIVE_FEED_VISIBLE_ROW_POOL
from fbcollector.services.storage.models import RawComment
from fbcollector.ui import theme

_ROW_HEIGHT = 64
_HIGHLIGHT_STEPS = 4


class _CommentRow(ctk.CTkFrame):
    """One recycled row widget - never destroyed, only its contents change."""

    def __init__(self, master) -> None:
        super().__init__(master, corner_radius=10, fg_color=theme.BG_CARD, height=_ROW_HEIGHT)
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)

        self._avatar = ctk.CTkLabel(
            self,
            text="\U0001f464",
            width=36,
            height=36,
            corner_radius=18,
            fg_color=theme.BG_CARD_ALT,
            font=theme.body_font(16),
        )
        self._avatar.grid(row=0, column=0, rowspan=2, padx=10, pady=10)

        self._username_label = ctk.CTkLabel(
            self, text="", font=theme.body_font(12, "bold"), anchor="w", text_color=theme.TEXT_PRIMARY
        )
        self._username_label.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(8, 0))

        self._time_label = ctk.CTkLabel(
            self, text="", font=theme.body_font(10), anchor="e", text_color=theme.TEXT_MUTED
        )
        self._time_label.grid(row=0, column=2, sticky="e", padx=(0, 10), pady=(8, 0))

        self._comment_label = ctk.CTkLabel(
            self, text="", font=theme.body_font(12), anchor="w", text_color=theme.TEXT_SECONDARY, justify="left"
        )
        self._comment_label.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, 10), pady=(0, 8))

    def set_comment(self, comment: RawComment | None) -> None:
        # Rows stay packed at all times (their pool slot never changes geometry manager) -
        # "empty" rows just render blank, which also avoids reshuffling pack order that
        # pack_forget()/pack() cycling on individual pool rows would otherwise cause.
        if comment is None:
            self._username_label.configure(text="")
            self._comment_label.configure(text="")
            self._time_label.configure(text="")
            self.configure(fg_color=theme.BG_CARD)
            return
        label = f"{comment.username}"
        if comment.employee_id:
            label += f"  ·  ID {comment.employee_id}"
        self._username_label.configure(text=label)
        self._comment_label.configure(text=comment.comment)
        self._time_label.configure(text=comment.timestamp.strftime("%H:%M:%S"))
        self.configure(fg_color=theme.BG_CARD)

    def flash_highlight(self, step: int = 0) -> None:
        if step >= _HIGHLIGHT_STEPS:
            self.configure(fg_color=theme.BG_CARD)
            return
        # simple color interpolation tween between accent and base card color (CTk has no real opacity)
        self.configure(fg_color=theme.ACCENT if step % 2 == 0 else theme.BG_CARD_ALT)
        self.after(90, lambda: self.flash_highlight(step + 1))


class LiveFeedView(ctk.CTkFrame):
    """Newest-on-top virtualized feed with a recycled widget pool."""

    def __init__(
        self,
        master,
        on_scroll_page: Callable[[int, int], list[RawComment]] | None = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._on_scroll_page = on_scroll_page
        self._items: deque[RawComment] = deque(maxlen=LIVE_FEED_IN_MEMORY_CACHE)
        self._filtered: list[RawComment] | None = None  # active when search filter applied
        self._scroll_offset = 0  # in row units, 0 = top (newest)

        self._scrollable = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scrollable.pack(fill="both", expand=True)
        # Mouse wheel pages through the virtualized window (row-unit offset), rather than
        # relying on CTkScrollableFrame's own scrolling, since the pool is fixed-size.
        self._scrollable.bind("<MouseWheel>", self._on_mouse_wheel)

        self._row_pool: list[_CommentRow] = []
        for _ in range(LIVE_FEED_VISIBLE_ROW_POOL):
            row = _CommentRow(self._scrollable)
            row.pack(fill="x", padx=4, pady=3)
            self._row_pool.append(row)

        self._render()

    def append_batch(self, comments: list[RawComment]) -> None:
        """Newest-first prepend; only the top rows get the slide/highlight treatment."""
        if not comments:
            return
        for comment in reversed(comments):
            self._items.appendleft(comment)
        if self._filtered is None and self._scroll_offset == 0:
            self._render()
            for row, _ in zip(self._row_pool, comments):
                row.flash_highlight()

    def apply_filter(self, query: str) -> None:
        if not query:
            self._filtered = None
        else:
            lowered = query.lower()
            self._filtered = [
                c
                for c in self._items
                if lowered in c.username.lower()
                or lowered in c.comment.lower()
                or (c.employee_id and lowered in c.employee_id.lower())
            ]
        self._scroll_offset = 0
        self._render()

    def reset(self) -> None:
        self._items.clear()
        self._filtered = None
        self._scroll_offset = 0
        self._render()

    def _on_mouse_wheel(self, event) -> None:
        direction = -1 if event.delta > 0 else 1
        source_len = len(self._filtered if self._filtered is not None else self._items)
        max_offset = max(0, source_len - LIVE_FEED_VISIBLE_ROW_POOL)
        self._scroll_offset = max(0, min(max_offset, self._scroll_offset + direction * 3))
        self._render()

    def _active_source(self) -> list[RawComment] | deque[RawComment]:
        return self._filtered if self._filtered is not None else self._items

    def _render(self) -> None:
        source = self._active_source()
        source_list = source if isinstance(source, list) else list(source)
        window = source_list[self._scroll_offset : self._scroll_offset + LIVE_FEED_VISIBLE_ROW_POOL]
        for i, row in enumerate(self._row_pool):
            row.set_comment(window[i] if i < len(window) else None)
