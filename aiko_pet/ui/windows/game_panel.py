"""Shared small window chrome for turn-based player panels, without rules."""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable

from ...games.contracts import SessionSummary
from ...pet.content import GERMAN_TEXT
from ..common.skin import AikoSkin
from ..common.window_drag import WindowDrag, bounded_position


class GamePanel:
    def __init__(
        self, root: tk.Tk, title: str, *, close: Callable[[], None],
        next_round: Callable[[], None], skin: AikoSkin, always_on_top: bool,
    ) -> None:
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg=skin.border)
        self.window.wm_attributes("-topmost", always_on_top)
        if sys.platform == "win32":
            self.window.wm_attributes("-toolwindow", True)
        self.window.bind("<Escape>", lambda _event: close())
        outer = skin.frame(self.window)
        outer.pack(fill="both", expand=True, padx=3, pady=3)
        header = skin.header(outer, title)
        header.pack(fill="x")
        self._drag = WindowDrag(self.window, header)
        self.body = skin.frame(outer)
        self.body.pack(fill="both", expand=True, padx=12, pady=10)
        self.status = tk.Label(
            outer, bg=skin.background, fg=skin.text, font=(skin.font, 10),
        )
        self.status.pack(fill="x", padx=10, pady=5)
        self.score = tk.Label(
            outer, bg=skin.background, fg=skin.text, font=(skin.font, 9),
        )
        self.score.pack(fill="x", padx=10, pady=5)
        self.next_button = skin.button(
            outer, GERMAN_TEXT.format("game.next"), next_round,
        )
        self.next_button.configure(state="disabled")
        self.next_button.pack(fill="x", padx=12, pady=4)
        skin.button(outer, GERMAN_TEXT.format("ui.close"), close).pack(
            anchor="e", padx=12, pady=(4, 10),
        )

    def show(self, root: tk.Tk) -> None:
        self.window.update_idletasks()
        width, height = self.window.winfo_reqwidth(), self.window.winfo_reqheight()
        x, y = bounded_position(
            root.winfo_rootx() + root.winfo_width() + 12,
            root.winfo_rooty() - height // 2, width, height,
            root.winfo_screenwidth(), root.winfo_screenheight(),
        )
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.deiconify()

    def update(self, score: SessionSummary, *, status: str, finished: bool) -> None:
        self.status.configure(text=status)
        self.score.configure(text=GERMAN_TEXT.format(
            "game.score", player=str(score.wins), aiko=str(score.losses),
            draws=str(score.draws),
        ))
        self.next_button.configure(state="normal" if finished else "disabled")

    def destroy(self) -> None:
        self._drag.close()
        self.window.destroy()
