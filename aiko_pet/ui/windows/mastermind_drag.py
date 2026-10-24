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
    ) -> None:
        self._images, self._drop = images, drop
        self._source: tk.Misc | None = None
        self._ghost: tk.Toplevel | None = None
        self._color: str | None = None
        self._slot: int | None = None

    def begin(
        self, event: tk.Event[tk.Misc], color: str, slot: int | None = None
    ) -> str:
        self.cancel()
        self._source, self._color, self._slot = event.widget, color, slot
        ghost = self._ghost = tk.Toplevel(event.widget)
        ghost.withdraw()
        ghost.overrideredirect(True)
        ghost.transient(event.widget.winfo_toplevel())
        ghost.wm_attributes("-topmost", True)
        background = "#010203"
        if sys.platform == "win32":
            ghost.wm_attributes("-transparentcolor", background)
        tk.Label(ghost, image=self._images.get(color), bd=0, bg=background).pack()
        self.motion(event)
        ghost.deiconify()
        event.widget.grab_set()
        return "break"

    def motion(self, event: tk.Event[tk.Misc]) -> str:
        if self._ghost is not None:
            self._ghost.geometry(f"+{event.x_root - 32}+{event.y_root - 32}")
        return "break"

    def release(self, event: tk.Event[tk.Misc]) -> str:
        color, slot = self._color, self._slot
        self.cancel()
        if color is not None:
            self._drop(color, slot, event.x_root, event.y_root)
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
