"""Native keyboard/button semantics with root-owned, projected VN artwork."""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable

from .icon_images import IconImages


def update_button_state(button: tk.Button, *, enabled: bool) -> None:
    """Project permission only when it changes; keep native enabled hover state."""
    if (button.cget("state") != "disabled") != enabled:
        button.configure(state="normal" if enabled else "disabled")


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
        align_left: bool = False,
    ) -> None:
        self._copy: tk.Label | None = None
        self._chevron: tk.Label | None = None
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
            compound="none" if align_left else "center",
            font=(font, 8 if size == "menu_back" else 10),
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
            wraplength=max(
                40, self._art["normal"].width() - (16 if size == "menu_back" else 80)
            ),
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
        self.bind("<Destroy>", self._destroyed, add="+")
        if align_left:
            left = 16 + icon.width() if icon is not None else 14
            copy_width = max(40, self._art["normal"].width() - left - 28)
            self._copy = tk.Label(
                self, font=(font, 10), fg="#3E4C61", anchor="w",
                justify="left", bd=0, padx=0, pady=0, cursor="hand2",
                wraplength=copy_width,
            )
            self._copy.place(
                x=left, rely=0.5, anchor="w", width=copy_width,
            )
            self._chevron = tk.Label(
                self, font=(font, 13), fg="#97667F", bd=0, padx=0, pady=0,
                cursor="hand2",
            )
            self._chevron.place(relx=1, x=-14, rely=0.5, anchor="e")
            for label in (self._copy, self._chevron):
                for sequence in (
                    "<Enter>", "<Leave>", "<ButtonPress-1>", "<ButtonRelease-1>",
                ):
                    label.bind(sequence, self._forward(sequence))
            self._set_copy()
            self._paint()

    def _forward(self, sequence: str) -> Callable[[tk.Event], None]:
        def forward(event: tk.Event) -> None:
            self.event_generate(
                sequence, x=event.x_root - self.winfo_rootx(),
                y=event.y_root - self.winfo_rooty(),
            )
        return forward

    def _set_copy(self) -> None:
        if self._copy is not None and self._chevron is not None:
            text = str(super().cget("text"))
            submenu = text.rstrip().endswith("›")
            self._copy.configure(
                text=text.rstrip(" ›") if submenu else text
            )
            self._chevron.configure(text="›" if submenu else "")

    def _destroyed(self, event: tk.Event) -> None:
        if event.widget is self:
            self._art.clear()

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
        if self._copy is not None and self._chevron is not None:
            art = self._art[state]
            color = art.get(art.width() // 2, art.height() // 2)
            background = "#{:02x}{:02x}{:02x}".format(*color)
            for label in (self._copy, self._chevron):
                label.configure(
                    bg=background,
                    fg="#817883" if state == "disabled" else "#3E4C61",
                )

    def set_selected(self, selected: bool) -> None:
        """Render an authoritative toggle; this is not another pin owner."""
        self._selected = selected
        self._paint()

    def configure(self, cnf: Any = None, **kwargs: Any) -> Any:
        result = super().configure(cnf, **kwargs)
        self._set_copy()
        if "state" in kwargs or isinstance(cnf, dict) and "state" in cnf:
            self._paint()
        return result
