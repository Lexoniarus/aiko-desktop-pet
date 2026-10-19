"""Transient game selection; opening this view never starts a session."""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable
from functools import partial

from ...games.contracts import GameId
from ...pet.content import GERMAN_TEXT
from ..common.skin import AikoSkin
from ..common.window_drag import bounded_position


class GameMenu:
    def __init__(
        self, root: tk.Tk, x: int, y: int, *,
        choices: tuple[GameId, ...], selected: Callable[[GameId], None],
        closed: Callable[[], None], always_on_top: bool, skin: AikoSkin,
    ) -> None:
        self._selected = selected
        self._on_closed = closed
        self._closed = False
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg=skin.border)
        self.window.wm_attributes("-topmost", always_on_top)
        if sys.platform == "win32":
            self.window.wm_attributes("-toolwindow", True)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.bind("<Escape>", lambda _event: self.close())
        body = skin.frame(self.window)
        body.pack(fill="both", expand=True, padx=3, pady=3)
        header = skin.header(body, GERMAN_TEXT.format("game.select"))
        header.configure(width=240, cursor="arrow")
        header.pack(fill="x")
        self.buttons: dict[GameId, tk.Button] = {}
        for game in choices:
            button = skin.button(
                body, GERMAN_TEXT.format(f"game.name.{game.value}"),
                partial(self.choose, game), size="wide",
            )
            button.pack(fill="x", padx=10, pady=4)
            self.buttons[game] = button
        skin.button(body, GERMAN_TEXT.format("ui.close"), self.close).pack(
            fill="x", padx=10, pady=(4, 8),
        )
        self.window.update_idletasks()
        x, y = bounded_position(
            x, y, self.window.winfo_reqwidth(), self.window.winfo_reqheight(),
            root.winfo_screenwidth(), root.winfo_screenheight() - 45,
        )
        self.window.geometry(f"+{x}+{y}")
        self.window.deiconify()
        self.window.focus_set()

    def choose(self, game: GameId) -> None:
        if not self._closed and game in self.buttons:
            self.close()
            self._selected(game)

    def contains_pointer(self, x: int, y: int) -> bool:
        if self._closed:
            return False
        return (
            self.window.winfo_rootx() <= x
            < self.window.winfo_rootx() + self.window.winfo_width()
            and self.window.winfo_rooty() <= y
            < self.window.winfo_rooty() + self.window.winfo_height()
        )

    def focus(self) -> None:
        self.window.lift()
        self.window.focus_set()

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self.window.destroy()
            self._on_closed()
