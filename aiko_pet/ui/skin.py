"""Shared Kenney appearance; widget owners still choose their own layout."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable

from ..asset_paths import KENNEY_UI_DIR


class AikoSkin:
    """Own one root-local set of images and the installed-font fallback."""

    background = "#D7DCE8"
    text = "#414B5F"
    muted = "#617189"
    panel = "#E9ECF5"
    accent = "#2998D4"
    border = "#8E9CB1"

    def __init__(self, root: tk.Tk) -> None:
        try:
            fonts = set(tkfont.families(root=root))
        except tk.TclError:
            fonts = set()
        self.font = "Kenney Mini" if "Kenney Mini" in fonts else "Segoe UI"
        self.banner = tk.PhotoImage(
            master=root, file=str(KENNEY_UI_DIR / "toolbar_banner.png"),
        )
        self.buttons = {
            name: tk.PhotoImage(
                master=root, file=str(KENNEY_UI_DIR / f"button_{name}.png"),
            )
            for name in ("regular", "wide", "small")
        }

    def frame(self, parent: tk.Misc) -> tk.Frame:
        return tk.Frame(
            parent, bg=self.background, highlightthickness=2,
            highlightbackground=self.panel, bd=0,
        )

    def header(self, parent: tk.Misc, text: str) -> tk.Label:
        return tk.Label(
            parent, text=text, image=self.banner, compound="center",
            font=(self.font, 10, "bold"), fg="#FFFFFF", bg=self.accent,
            padx=14, cursor="fleur",
        )

    def button(
        self, parent: tk.Misc, text: str, command: Callable[[], None], *,
        size: str = "regular",
    ) -> tk.Button:
        return tk.Button(
            parent, text=text, command=command, image=self.buttons[size],
            compound="center", font=(self.font, 9), fg=self.text,
            bg=self.background, activeforeground="#0B6DAA",
            activebackground=self.background, bd=0, relief="flat",
            padx=0, pady=0, highlightthickness=0, cursor="hand2",
        )
