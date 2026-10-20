"""Accessible passive descriptions inside the existing window, no new Toplevel."""

from __future__ import annotations

import tkinter as tk
from functools import partial
from typing import Callable

from .skin import AikoSkin


def tip_position(
    x: int,
    top: int,
    bottom: int,
    width: int,
    height: int,
    available_width: int,
    available_height: int,
) -> tuple[int, int]:
    left = max(0, min(x, available_width - width))
    y = bottom + 4 if bottom + 4 + height <= available_height else top - height - 4
    return left, max(0, min(y, available_height - height))


class DescriptionTip:
    def __init__(self, parent: tk.Misc, skin: AikoSkin) -> None:
        self._parent = parent
        self._frame = tk.Frame(
            parent,
            bg="#FFFCFD",
            highlightthickness=1,
            highlightbackground=skin.border,
            padx=12,
            pady=9,
        )
        self._label = tk.Label(
            self._frame,
            bg="#FFFCFD",
            fg=skin.text,
            font=(skin.font, 9),
            justify="left",
            anchor="w",
        )
        self._label.pack(fill="both", expand=True)
        self._anchor: tk.Widget | None = None
        parent.bind("<Unmap>", lambda _e: self.hide(), add="+")

    def attach(self, widget: tk.Widget, text: Callable[[], str]) -> None:
        widget.configure({"takefocus": True})
        for sequence in ("<Enter>", "<FocusIn>"):
            widget.bind(sequence, partial(self._show_event, widget, text), add="+")
        for sequence in ("<Leave>", "<FocusOut>", "<Escape>"):
            widget.bind(sequence, lambda _e: self.hide(), add="+")
        for sequence in ("<Button-1>", "<Return>", "<space>"):
            widget.bind(sequence, partial(self._toggle_event, widget, text), add="+")

    def _show_event(
        self, widget: tk.Widget, text: Callable[[], str], _event: tk.Event
    ) -> None:
        self.show(widget, text())

    def _toggle_event(
        self, widget: tk.Widget, text: Callable[[], str], _event: tk.Event
    ) -> None:
        self.toggle(widget, text())

    def toggle(self, widget: tk.Widget, text: str) -> None:
        if self._anchor is widget:
            self.hide()
        else:
            self.show(widget, text)

    def show(self, widget: tk.Widget, text: str) -> None:
        width = min(320, max(80, self._parent.winfo_width() - 12))
        self._label.configure(text=text, wraplength=width - 24)
        self._frame.update_idletasks()
        x, y = tip_position(
            widget.winfo_rootx() - self._parent.winfo_rootx(),
            widget.winfo_rooty() - self._parent.winfo_rooty(),
            widget.winfo_rooty() - self._parent.winfo_rooty() + widget.winfo_height(),
            width,
            self._frame.winfo_reqheight(),
            self._parent.winfo_width(),
            self._parent.winfo_height(),
        )
        self._frame.place(x=x, y=y, width=width)
        self._frame.lift()
        self._anchor = widget

    def hide(self) -> None:
        self._frame.place_forget()
        self._anchor = None
