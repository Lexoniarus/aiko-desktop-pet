"""Native keyboard/button semantics with root-owned, projected VN artwork."""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable

from .icon_images import IconImages


class ImageButton(tk.Button):
    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        *,
        images: IconImages,
        size: str,
        font: str,
        icon: tk.PhotoImage | None = None,
    ) -> None:
        self._art = {
            state: images.button_art(state, size, icon)
            for state in ("normal", "hover", "pressed", "disabled", "active")
        }
        self._hover = False
        self._pressed = False
        self._selected = False
        super().__init__(
            parent,
            text=text,
            command=command,
            image=self._art["normal"],
            compound="center",
            font=(font, 10),
            fg="#3E4C61",
            bg="#FCF7F9",
            activebackground="#FCF7F9",
            activeforeground="#3E4C61",
            disabledforeground="#817883",
            bd=0,
            relief="flat",
            cursor="hand2",
            highlightthickness=2,
            highlightbackground="#FCF7F9",
            highlightcolor="#657F9D",
            takefocus=True,
            wraplength=max(40, self._art["normal"].width() - 80),
        )
        self.bind("<Enter>", lambda _e: self._feedback(hover=True), add="+")
        self.bind(
            "<Leave>", lambda _e: self._feedback(hover=False, pressed=False), add="+"
        )
        for sequence in ("<ButtonPress-1>", "<KeyPress-space>"):
            self.bind(sequence, lambda _e: self._feedback(pressed=True), add="+")
        for sequence in ("<ButtonRelease-1>", "<KeyRelease-space>"):
            self.bind(sequence, lambda _e: self._feedback(pressed=False), add="+")
        self.bind("<Return>", lambda _e: self.invoke())

    def _feedback(
        self, *, hover: bool | None = None, pressed: bool | None = None
    ) -> None:
        if hover is not None:
            self._hover = hover
        if pressed is not None:
            self._pressed = pressed
        self._paint()

    def _paint(self) -> None:
        state = (
            "disabled"
            if self.cget("state") == "disabled"
            else "active"
            if self._selected
            else "pressed"
            if self._pressed
            else "hover"
            if self._hover
            else "normal"
        )
        super().configure(image=self._art[state])

    def set_selected(self, selected: bool) -> None:
        """Render an authoritative toggle; this is not another pin owner."""
        self._selected = selected
        self._paint()

    def configure(self, cnf: Any = None, **kwargs: Any) -> Any:
        result = super().configure(cnf, **kwargs)
        if "state" in kwargs:
            self._paint()
        return result
