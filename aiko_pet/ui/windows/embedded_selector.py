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
        self._surface = skin.surface(parent)
        self.frame = self._surface.frame
        self.frame.pack(fill="both", expand=True)
        header = tk.Frame(self._surface.body, bg=skin.background)
        header.pack(fill="x")
        self.back = skin.button(
            header, GERMAN_TEXT.format("vn.back"), self.close, size="menu_back"
        )
        self.back.pack(side="right")
        tk.Label(
            header,
            text=title,
            bg=skin.background,
            fg=skin.text,
            font=(skin.font, 10, "bold"),
            anchor="w",
        ).pack(side="left", pady=5)
        self.scroll = ScrollRegion(
            self._surface.body, skin, width=230, height=240, autohide=True,
        )
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
