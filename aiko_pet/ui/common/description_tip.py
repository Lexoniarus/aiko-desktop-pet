"""Accessible passive descriptions inside the existing window, no new Toplevel."""

from __future__ import annotations

import tkinter as tk
from functools import partial
from typing import Callable

from . import scaled_widgets as scaled
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
        self._scale = skin.scale
        self._surface = skin.surface(parent)
        self._frame = self._surface.frame
        self._label = scaled.Label(
            self._surface.body,
            bg=skin.background,
            fg=skin.text,
            font=(skin.font, 9),
            justify="left",
            anchor="w",
        )
        self._label.pack(fill="both", expand=True)
        self._anchor: tk.Widget | None = None
        self._frame.bind("<Leave>", self._pointer_left, add="+")
        parent.bind("<Unmap>", lambda _e: self.hide(), add="+")

    def attach(
        self, widget: tk.Widget, text: Callable[[], str], *, focusable: bool = True,
    ) -> None:
        widget.configure({"takefocus": focusable})
        for sequence in ("<Enter>", "<FocusIn>"):
            widget.bind(sequence, partial(self._show_event, widget, text), add="+")
        widget.bind("<Leave>", self._pointer_left, add="+")
        for sequence in ("<FocusOut>", "<Escape>"):
            widget.bind(sequence, lambda _e: self.hide(), add="+")
        for sequence in ("<Button-1>", "<Return>", "<space>"):
            widget.bind(sequence, partial(self._toggle_event, widget, text), add="+")

    def _pointer_left(self, _event: tk.Event) -> None:
        """An overlapping description retains hover until both regions are left."""
        if self._anchor is None:
            return
        px, py = self._parent.winfo_pointerx(), self._parent.winfo_pointery()
        for widget in (self._anchor, self._frame):
            if not widget.winfo_ismapped():
                continue
            x, y = widget.winfo_rootx(), widget.winfo_rooty()
            if (x <= px < x + widget.winfo_width()
                    and y <= py < y + widget.winfo_height()):
                return
        self.hide()

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
        width = min(self._scale.pixels(420), max(
            self._scale.pixels(80), self._parent.winfo_width() - self._scale.pixels(12),
        ))
        self._label.configure(text=text, wraplength=self._scale.logical(width) - 24)
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
        self._frame.place(
            x=self._scale.logical(x), y=self._scale.logical(y),
            width=self._scale.logical(width),
        )
        self._frame.lift()
        self._anchor = widget

    def hide(self) -> None:
        self._frame.place_forget()
        self._anchor = None
