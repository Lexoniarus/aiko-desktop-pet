"""Title-only dragging shared by independently owned Tk utility windows."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from .window_geometry import BoundsAt


def bounded_position(
    x: int, y: int, width: int, height: int,
    screen_width: int, screen_height: int,
) -> tuple[int, int]:
    """Keep the title reachable even when a window exceeds the display."""
    return (
        max(0, min(x, screen_width - width)),
        max(0, min(y, screen_height - height)),
    )


class WindowDrag:
    """Own pointer deltas, never application settings or window visibility."""

    def __init__(
        self, window: tk.Toplevel, handle: tk.Widget, *,
        moved: Callable[[], None] | None = None,
        dropped: Callable[[int, int], None] | None = None,
        bounds_at: BoundsAt | None = None,
        handles: tuple[tk.Widget, ...] = (),
    ) -> None:
        self._window = window
        self._handle = handle
        self._moved = moved
        self._dropped = dropped
        self._bounds_at = bounds_at
        self._origin: tuple[int, int, int, int] | None = None
        self._position: tuple[int, int] | None = None
        self._closed = False
        self._bindings = []
        for widget in (handle, *handles):
            for sequence, callback in (
                ("<ButtonPress-1>", self.start),
                ("<B1-Motion>", self.move),
                ("<ButtonRelease-1>", self.finish),
            ):
                self._bindings.append((
                    widget, sequence, widget.bind(sequence, callback, add="+"),
                ))
            widget.configure({"cursor": "fleur"})

    @property
    def dragging(self) -> bool:
        return self._origin is not None

    def start(self, event: tk.Event) -> None:
        if self._closed:
            return
        self._position = (
            self._window.winfo_rootx(), self._window.winfo_rooty(),
        )
        self._origin = (event.x_root, event.y_root, *self._position)

    def move(self, event: tk.Event) -> None:
        origin = self._origin
        if origin is None or self._closed:
            return
        x = origin[2] + event.x_root - origin[0]
        y = origin[3] + event.y_root - origin[1]
        if self._bounds_at is None:
            self._position = bounded_position(
                x, y, self._window.winfo_width(), self._window.winfo_height(),
                self._window.winfo_screenwidth(), self._window.winfo_screenheight(),
            )
        else:
            self._position = self._bounds_at(event.x_root, event.y_root).clamp(
                x, y, self._window.winfo_width(), self._window.winfo_height(),
            )
        x, y = self._position
        # Explicit +negative coordinates are absolute Tk positions on left monitors.
        self._window.geometry(f"+{x}+{y}")
        if self._moved is not None:
            self._moved()

    def finish(self, _event: tk.Event) -> None:
        if self._origin is None or self._closed:
            return
        self._origin = None
        if self._dropped is not None and self._position is not None:
            self._dropped(*self._position)

    def close(self) -> None:
        """Release only this object's bindings, including a half-finished drag."""
        if self._closed:
            return
        self._closed = True
        self._origin = None
        for widget, sequence, identifier in self._bindings:
            if identifier:
                widget.unbind(sequence, identifier)
        self._bindings.clear()
