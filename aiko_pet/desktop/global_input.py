"""Poll only mouse button presses for dismissing floating desktop controls.

On Windows, Tk does not receive mouse events from other applications. Polling
mouse button *states* avoids installing hooks or examining keyboard input.
"""

from __future__ import annotations

import ctypes
import sys
from typing import Callable

VK_LBUTTON = 0x01
VK_RBUTTON = 0x02


class GlobalMouseClicks:
    """Report a new system-wide left/right click, including short taps."""

    def __init__(self, reader: Callable[[int], int] | None = None) -> None:
        self._reader: Callable[[int], int] | None
        if reader is not None:
            self._reader = reader
        elif sys.platform == "win32":
            try:
                self._reader = ctypes.windll.user32.GetAsyncKeyState
            except (AttributeError, OSError):
                self._reader = None
        else:
            self._reader = None
        self._previous_down: tuple[bool, bool] | None = None

    def clicked(self) -> bool:
        """Consume a new click edge; the first poll establishes a baseline."""
        if self._reader is None:
            return False
        try:
            states = (
                int(self._reader(VK_LBUTTON)) & 0xFFFF,
                int(self._reader(VK_RBUTTON)) & 0xFFFF,
            )
        except (AttributeError, OSError, ValueError):
            return False
        downs = (
            bool(states[0] & 0x8000),
            bool(states[1] & 0x8000),
        )
        previous = self._previous_down
        self._previous_down = downs
        if previous is None:
            return False
        return any(
            (pressed and not old_down) or (state & 0x0001)
            for pressed, old_down, state in zip(downs, previous, states)
        )


def idle_seconds_windows() -> float | None:
    """Duration since *any* user input; never reads text or key identities."""
    if sys.platform != "win32":
        return None

    class LastInputInfo(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint32)]

    info = LastInputInfo()
    info.cbSize = ctypes.sizeof(info)
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        if not user32.GetLastInputInfo(ctypes.byref(info)):
            return None
        kernel32.GetTickCount.restype = ctypes.c_uint32
        elapsed_ms = (int(kernel32.GetTickCount()) - int(info.dwTime)) & 0xFFFFFFFF
        return elapsed_ms / 1000.0
    except (AttributeError, OSError, ValueError):
        return None
