"""One native widget owns artwork, icon, text, focus and button interaction."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

from .icon_images import IconImages


def update_button_state(button: tk.Button | ttk.Button, *, enabled: bool) -> None:
    """Project permission only when it changes; keep native enabled hover state."""
    if (button.cget("state") != "disabled") != enabled:
        button.configure(state="normal" if enabled else "disabled")


class ImageButton(ttk.Button):
    def __init__(
        self, parent: tk.Misc, text: str, command: Callable[[], None], *,
        images: IconImages, size: str, font: str, icon: tk.PhotoImage | None = None,
        align_left: bool = False, stacked: bool = False,
    ) -> None:
        self._images, self._size, self._font = images, size, font
        self._icon_width = icon.width() if icon is not None else 0
        self._align_left, self._stacked = align_left, stacked
        self._text = text
        super().__init__(
            parent, text=self._label(text), command=command, width=0,
            # An explicit disabled image avoids Tk's generated stippled copy.
            image=f"{icon} disabled {icon}" if icon is not None else "",
            compound="top" if stacked else "left" if icon is not None else "none",
            style=self._style(text), cursor="hand2", takefocus=True,
        )
        self.bind("<Return>", lambda _event: self.invoke())

    def _label(self, text: str) -> str:
        return text.rstrip(" ›") if self._align_left else text

    def _style(self, text: str) -> str:
        return self._images.buttons.button(
            self._size, self._font, self._icon_width,
            align_left=self._align_left, stacked=self._stacked,
            submenu=self._align_left and text.rstrip().endswith("›"),
        )

    def set_selected(self, selected: bool) -> None:
        """Native selected state survives hover, presses and disabled state."""
        self.state(["selected" if selected else "!selected"])

    def cget(self, key: str) -> Any:
        if key == "text":
            return self._text
        if key == "state":
            return "disabled" if self.instate(["disabled"]) else "normal"
        return super().cget(key)

    def configure(self, cnf: Any = None, **kwargs: Any) -> Any:
        if cnf is None and not kwargs or isinstance(cnf, str):
            return super().configure(cnf, **kwargs)
        options = dict(cnf or {})
        options.update(kwargs)
        if "text" in options:
            self._text = str(options["text"])
            options["text"] = self._label(self._text)
            options["style"] = self._style(self._text)
        return super().configure(**options)

    config = configure
