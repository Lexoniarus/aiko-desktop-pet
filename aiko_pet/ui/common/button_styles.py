"""Root-local VN styles; native ttk draws each complete button in one window."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from tkinter.ttk import _Layout


class ButtonStyles:
    def __init__(self, root: tk.Tk, surface: Callable[[str], tk.PhotoImage]) -> None:
        self.style = ttk.Style(root)
        self._surface = surface
        self._prefix = f"Aiko{id(self)}"
        self._styles: dict[tuple[str, str, int, bool, bool, bool], str] = {}
        self._arrow = tk.PhotoImage(master=root, width=10, height=16)
        for y in range(3, 13):
            x = 2 + min(y - 3, 12 - y)
            self._arrow.put("#97667F", to=(x, y, x + 2, y + 1))
        self._arrow_element = f"{self._prefix}.arrow"
        self.style.element_create(self._arrow_element, "image", self._arrow)

    def button(
        self, size: str, font: str, icon_width: int, *,
        align_left: bool, stacked: bool, submenu: bool,
    ) -> str:
        key = size, font, icon_width, align_left, stacked, submenu
        if key in self._styles:
            return self._styles[key]
        art = {
            state: self._surface(f"button_{state}.{size}")
            for state in ("normal", "hover", "pressed", "disabled", "active")
        }
        frame = f"{self._prefix}.{len(self._styles)}.frame"
        name = f"{self._prefix}.{len(self._styles)}.TButton"
        self.style.element_create(
            frame, "image", art["normal"],
            ("disabled", art["disabled"]), ("selected", art["active"]),
            ("pressed", art["pressed"]), ("active", art["hover"]),
            border=min(18, art["normal"].height() // 3), padding=0, sticky="nsew",
        )
        children: list[tuple[str, _Layout | None]] = []
        if submenu:
            children.append((self._arrow_element, {"side": "right", "sticky": "e"}))
        children.append(("Button.label", {"sticky": "nsew"}))
        self.style.layout(name, [(frame, {"sticky": "nsew", "children": [
            ("Button.focus", {"sticky": "nsew", "children": [
                ("Button.padding", {"sticky": "nsew", "children": children}),
            ]}),
        ]})])
        wrap = max(24, art["normal"].width() - 24 - (12 if submenu else 0)
                   - (icon_width + 8 if icon_width and not stacked else 0))
        self.style.configure(
            name, font=(font, 8 if size == "menu_back" else 10),
            foreground="#3E4C61", background="#FCF7F9", borderwidth=0,
            padding=(10, 4, 12, 4), space=8, wraplength=wrap,
            anchor="w" if align_left else "center",
            justify="left" if align_left else "center",
            focusthickness=1, focuscolor="#657F9D", embossed=False, stipple="",
        )
        self.style.map(name, foreground=[("disabled", "#817883")])
        self._styles[key] = name
        return name
