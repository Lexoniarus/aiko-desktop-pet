"""One small Kenney food selector; it never mutates needs directly."""

from __future__ import annotations

import sys
import tkinter as tk
from typing import Callable

from ..presentation.food_models import FoodChoice, FoodId
from .skin import AikoSkin
from .window_drag import WindowDrag, bounded_position


class FoodMenu:
    """Read-only choices and a typed callback into the care application."""

    def __init__(
        self, root: tk.Tk, x: int, y: int, *,
        choices: tuple[FoodChoice, ...],
        selected: Callable[[FoodId], None],
        closed: Callable[[], None],
        always_on_top: bool,
        skin: AikoSkin,
    ) -> None:
        self._selected = selected
        self._closed_callback = closed
        self._closed = False
        self.skin = skin
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg=skin.border)
        self.window.wm_attributes("-topmost", always_on_top)
        if sys.platform == "win32":
            self.window.wm_attributes("-toolwindow", True)
        self.window.bind("<Escape>", lambda _event: self.close())
        outer = skin.frame(self.window)
        outer.pack(fill="both", expand=True, padx=3, pady=3)
        header = skin.header(outer, "WAS MÖCHTEST DU ESSEN?")
        header.pack(fill="x")
        self._drag = WindowDrag(self.window, header)
        body = tk.Frame(outer, bg=skin.background)
        body.pack(fill="both", expand=True, padx=9, pady=9)
        self.images: dict[str, tk.PhotoImage] = {}
        self.buttons: dict[str, tk.Button] = {}
        for column, choice in enumerate(choices):
            item = tk.Frame(body, bg=skin.panel, padx=5, pady=6)
            item.grid(row=0, column=column, padx=3, sticky="nsew")
            body.columnconfigure(column, weight=1)
            image = (
                tk.PhotoImage(master=root, file=str(choice.image_path))
                if choice.image_path.is_file() else None
            )
            if image is not None:
                self.images[choice.id] = image
            button = tk.Button(
                item, text=choice.name, image=image,
                compound="top", command=(
                    lambda food_id=choice.id: self.choose(food_id)
                ),
                font=(skin.font, 9), fg=skin.text,
                bg=skin.panel, activebackground=skin.background,
                activeforeground=skin.accent,
                bd=0, cursor="hand2", padx=5, pady=4,
            )
            button.pack(fill="x")
            self.buttons[choice.id] = button
            tk.Label(
                item, text=(
                    f"+{choice.satiety_points:.0f} · {choice.category_label}"
                ),
                bg=skin.panel, fg=skin.muted,
                font=(skin.font, 8),
            ).pack(pady=(1, 4))
        skin.button(outer, "Schließen", self.close).pack(
            anchor="e", padx=12, pady=(0, 8),
        )
        self.window.update_idletasks()
        width, height = self.window.winfo_reqwidth(), self.window.winfo_reqheight()
        tx, ty = bounded_position(
            x, y, width, height,
            root.winfo_screenwidth(), root.winfo_screenheight(),
        )
        self.window.geometry(f"+{tx}+{ty}")
        self.window.deiconify()

    def choose(self, food_id: FoodId) -> None:
        if self._closed:
            return
        self.close()
        self._selected(food_id)

    def contains_pointer(self, x: int, y: int) -> bool:
        if self._closed:
            return False
        left, top = self.window.winfo_rootx(), self.window.winfo_rooty()
        return (
            left <= x < left + self.window.winfo_width()
            and top <= y < top + self.window.winfo_height()
        )

    def focus(self) -> None:
        if not self._closed:
            self.window.lift()
            self.window.focus_set()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._drag.close()
        self.window.destroy()
        self._closed_callback()
