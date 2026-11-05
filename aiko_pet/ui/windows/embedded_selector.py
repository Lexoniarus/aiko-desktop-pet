"""Selection content inside a docked panel; HoverUi owns which menu is open."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from ...pet.content import GERMAN_TEXT
from ..common import scaled_widgets as scaled
from ..common.content_region import ContentRegion
from ..common.skin import AikoSkin
from .hover_contracts import SelectorCloseReason


class EmbeddedSelector:
    def __init__(
        self,
        parent: tk.Frame,
        skin: AikoSkin,
        *,
        title: str,
        closed: Callable[[SelectorCloseReason], None],
    ) -> None:
        self._closed = False
        self._on_closed = closed
        self._surface = skin.surface(parent)
        self.frame = self._surface.frame
        self.frame.pack(fill="both", expand=True)
        header = scaled.Frame(self._surface.body, bg=skin.background)
        header.pack(fill="x")
        self.back = skin.button(
            header, GERMAN_TEXT.format("vn.back"), self.close, size="menu_back"
        )
        # Back closes this selection through the existing lifetime callback.
        self.back.pack(side="left", padx=(0, 8))
        scaled.Label(
            header,
            text=title,
            bg=skin.background,
            fg=skin.text,
            font=(skin.font, 10, "bold"),
            anchor="w",
        ).pack(side="left", pady=5)
        self.content = ContentRegion(
            self._surface.body, skin,
        )
        self.content.frame.pack(fill="both", expand=True)

    def place_choice(self, button: tk.Widget, index: int) -> None:
        column, row = divmod(index, 3)
        self.content.body.grid_columnconfigure(column, weight=1, uniform="choices")
        button.grid(row=row, column=column, sticky="nsew", padx=3, pady=3)

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

    def close(self, reason: SelectorCloseReason = "explicit") -> None:
        if not self._closed:
            self._closed = True
            self.frame.destroy()
            self._on_closed(reason)
