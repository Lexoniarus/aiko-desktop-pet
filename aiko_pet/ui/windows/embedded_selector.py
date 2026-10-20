"""Embedded selection view; the existing HoverUi owns which menu is open."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from ...pet.content import GERMAN_TEXT
from ..common.scroll_region import ScrollRegion
from ..common.skin import AikoSkin


class EmbeddedSelector:
    def __init__(
        self,
        parent: tk.Frame,
        skin: AikoSkin,
        *,
        title: str,
        closed: Callable[[], None],
    ) -> None:
        self._closed = False
        self._on_closed = closed
        self.frame = tk.Frame(parent, bg=skin.background)
        self.frame.pack(fill="both", expand=True)
        self.back = skin.button(
            self.frame, GERMAN_TEXT.format("vn.back"), self.close, size="action"
        )
        self.back.pack(fill="x")
        tk.Label(
            self.frame,
            text=title,
            bg=skin.background,
            fg=skin.text,
            font=(skin.font, 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=5)
        self.scroll = ScrollRegion(self.frame, skin, width=242, height=240)
        self.scroll.frame.pack(fill="both", expand=True)

    def contains_pointer(self, x: int, y: int) -> bool:
        return not self._closed and (
            self.frame.winfo_rootx()
            <= x
            < self.frame.winfo_rootx() + self.frame.winfo_width()
            and self.frame.winfo_rooty()
            <= y
            < self.frame.winfo_rooty() + self.frame.winfo_height()
        )

    def focus(self) -> None:
        if not self._closed:
            self.back.focus_set()

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self.frame.destroy()
            self._on_closed()
