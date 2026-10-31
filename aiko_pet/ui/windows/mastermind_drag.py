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
        try:
            event.widget.grab_set()
        except tk.TclError:
            self.cancel()
            raise
        return "break"

    def _show_ghost(self) -> None:
        assert self._source is not None
        # A grab includes its widget descendants. Keep the preview outside that
        # subtree so motion/release over its label still reach the source canvas.
        owner = self._source.winfo_toplevel()
        ghost = self._ghost = tk.Toplevel(owner)
        ghost.withdraw()
        ghost.overrideredirect(True)
        ghost.transient(owner)
        ghost.wm_attributes("-topmost", True)
        background = "#010203"
        if sys.platform == "win32":
            ghost.wm_attributes("-transparentcolor", background)
        tk.Label(ghost, image=self._images.get(self._color), bd=0, bg=background).pack()

    def _moved(self, event: tk.Event[tk.Misc]) -> bool:
        x, y = self._origin
        return (event.x_root - x) ** 2 + (event.y_root - y) ** 2 >= 36

    def motion(self, event: tk.Event[tk.Misc]) -> str:
        try:
            if self._source is not None and self._ghost is None and self._moved(event):
                self._show_ghost()
            if self._ghost is not None:
                self._ghost.geometry(f"+{event.x_root - 32}+{event.y_root - 32}")
                self._ghost.deiconify()
                self._ghost.lift()
        except Exception:
            self.cancel()
            raise
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
        source, ghost = self._source, self._ghost
        self._source, self._ghost = None, None
        self._color, self._slot = None, None
        try:
            if source is not None and str(
                source.tk.call("grab", "current", source)
            ) == str(source):
                source.grab_release()
        except tk.TclError:
            # The source may already have been destroyed during window closure.
            pass
        finally:
            if ghost is not None:
                try:
                    ghost.destroy()
                except tk.TclError:
                    pass
