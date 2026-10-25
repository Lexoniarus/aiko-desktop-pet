"""Local Tk drag without global input hooks or interaction with world objects."""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable

from ..common.mastermind_images import MastermindImages


class MastermindDrag:
    def __init__(
        self,
        images: MastermindImages,
        drop: Callable[[str, int | None, int, int], None],
        click: Callable[[str, int | None], None],
    ) -> None:
        self._images, self._drop, self._click = images, drop, click
        self._source: tk.Misc | None = None
        self._ghost: tk.Toplevel | None = None
        self._color: str | None = None
        self._slot: int | None = None
        self._origin = (0, 0)

    def begin(
        self, event: tk.Event[tk.Misc], color: str, slot: int | None = None
    ) -> str:
        self.cancel()
        self._source, self._color, self._slot = event.widget, color, slot
        self._origin = event.x_root, event.y_root
        event.widget.grab_set()
        return "break"

    def _show_ghost(self) -> None:
        assert self._source is not None
        ghost = self._ghost = tk.Toplevel(self._source)
        ghost.withdraw()
        ghost.overrideredirect(True)
        ghost.transient(self._source.winfo_toplevel())
        ghost.wm_attributes("-topmost", True)
        background = "#010203"
        if sys.platform == "win32":
            ghost.wm_attributes("-transparentcolor", background)
        tk.Label(ghost, image=self._images.get(self._color), bd=0, bg=background).pack()

    def _moved(self, event: tk.Event[tk.Misc]) -> bool:
        x, y = self._origin
        return (event.x_root - x) ** 2 + (event.y_root - y) ** 2 >= 36

    def motion(self, event: tk.Event[tk.Misc]) -> str:
        if self._source is not None and self._ghost is None and self._moved(event):
            try:
                self._show_ghost()
            except Exception:
                self.cancel()
                raise
        if self._ghost is not None:
            self._ghost.geometry(f"+{event.x_root - 32}+{event.y_root - 32}")
            self._ghost.deiconify()
            self._ghost.lift()
        return "break"

    def release(self, event: tk.Event[tk.Misc]) -> str:
        color, slot = self._color, self._slot
        dragged = self._ghost is not None or self._moved(event)
        self.cancel()
        if color is not None:
            if dragged:
                self._drop(color, slot, event.x_root, event.y_root)
            else:
                self._click(color, slot)
        return "break"

    def cancel(self) -> None:
        if self._source is not None:
            if str(self._source.tk.call("grab", "current", self._source)) == str(
                self._source
            ):
                self._source.grab_release()
            self._source = None
        if self._ghost is not None:
            self._ghost.destroy()
            self._ghost = None
        self._color, self._slot = None, None
