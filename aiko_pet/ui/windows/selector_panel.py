"""A toolbar-owned popup whose requested size never enters the toolbar layout."""

from __future__ import annotations

import sys
import tkinter as tk
from typing import Callable

from ..common import scaled_widgets as scaled
from ..common.skin import AikoSkin
from ...presentation.geometry import BoundsAt, WindowBounds
from .hover_contracts import SelectorCloseReason


class SelectorPanel:
    def __init__(
        self, owner: tk.Toplevel, skin: AikoSkin, *,
        closed: Callable[[SelectorCloseReason], None],
        bounds_at: BoundsAt | None = None,
        anchor: tk.Widget | None = None,
    ) -> None:
        self._owner, self._skin = owner, skin
        self._bounds_at = bounds_at
        self._anchor = anchor if anchor is not None else owner
        self._anchor_binding: str | None = self._anchor.bind(
            "<Configure>", lambda _event: self.place(), add="+",
        )
        self.window = tk.Toplevel(owner)
        self.window.withdraw()
        self.window.title("Aiko · Auswahl")
        self.window.overrideredirect(True)
        self.window.configure(bg=skin.border)
        self.window.wm_attributes("-topmost", owner.wm_attributes("-topmost"))
        if sys.platform == "win32":
            self.window.wm_attributes("-toolwindow", True)
        self.body = scaled.Frame(self.window, bg=skin.background)
        self.body.pack(fill="both", expand=True, padx=1, pady=1)
        self.window.bind("<Escape>", lambda _event: closed("explicit"))
        self.window.bind("<Configure>", self._configured, add="+")
        self._position: tuple[int, int] | None = None
        # Build the choices before first mapping, including callers constructing
        # a selector directly. This one idle callback is cancelled on close.
        self._pending: str | None = self.window.after_idle(self.show)

    def show(self) -> None:
        if self._pending is not None:
            self.window.after_cancel(self._pending)
            self._pending = None
        self.window.update_idletasks()
        self.place()
        self.window.deiconify()

    def _configured(self, event: tk.Event) -> None:
        if event.widget is self.window:
            self.place()

    def place(self) -> None:
        owner = self._owner
        x, y = owner.winfo_rootx(), owner.winfo_rooty()
        owner_width, owner_height = owner.winfo_width(), owner.winfo_height()
        width, height = self.window.winfo_reqwidth(), self.window.winfo_reqheight()
        bounds = (
            self._bounds_at(x + owner_width // 2, y + owner_height // 2)
            if self._bounds_at is not None else
            WindowBounds(0, 0, owner.winfo_screenwidth(), owner.winfo_screenheight())
        )
        gap = max(1, self._skin.scale.pixels(4))
        right, left = x + owner_width + gap, x - width - gap
        if right + width <= bounds.right:
            target = right
        elif left >= bounds.left:
            target = left
        else:
            target = right if bounds.right - right >= x - bounds.left else left
        position = bounds.clamp(target, self._anchor.winfo_rooty(), width, height)
        if position != self._position:
            self.window.geometry(f"+{position[0]}+{position[1]}")
            self._position = position

    def contains_pointer(self, x: int, y: int) -> bool:
        if not self.window.winfo_ismapped():
            return False
        left, top = self.window.winfo_rootx(), self.window.winfo_rooty()
        right, bottom = (left + self.window.winfo_width(),
                         top + self.window.winfo_height())
        if left <= x < right and top <= y < bottom:
            return True
        # The narrow seam is part of the same hover area.
        owner_left, owner_top = (self._owner.winfo_rootx(),
                                 self._owner.winfo_rooty())
        owner_right = owner_left + self._owner.winfo_width()
        bridge_left, bridge_right = (
            (owner_right, left) if left >= owner_right else (right, owner_left)
        )
        return (
            bridge_left <= x < bridge_right
            and max(top, owner_top) <= y
            < min(bottom, owner_top + self._owner.winfo_height())
        )

    def close(self) -> None:
        if self._anchor_binding is not None:
            self._anchor.unbind("<Configure>", self._anchor_binding)
            self._anchor_binding = None
        if self._pending is not None:
            self.window.after_cancel(self._pending)
            self._pending = None
        self.window.destroy()
