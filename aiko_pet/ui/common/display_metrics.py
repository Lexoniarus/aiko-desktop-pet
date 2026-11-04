"""Read Windows DPI virtualization without changing process/window awareness."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes


def virtualization_factor() -> float:
    """Tk coordinates need conversion only for a DPI-unaware process."""
    if sys.platform != "win32":
        return 1.0
    try:
        shcore = ctypes.WinDLL("shcore", use_last_error=True)
        awareness = ctypes.c_int()
        if shcore.GetProcessDpiAwareness(None, ctypes.byref(awareness)) != 0:
            return 1.0
        if awareness.value != 0:
            return 1.0
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
        user32.MonitorFromPoint.restype = wintypes.HANDLE
        shcore.GetScaleFactorForMonitor.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(ctypes.c_int),
        ]
        # Tk's screen dimensions describe the primary display, not virtual bounds.
        monitor = user32.MonitorFromPoint(wintypes.POINT(0, 0), 1)
        percent = ctypes.c_int(100)
        if not monitor or shcore.GetScaleFactorForMonitor(
            monitor, ctypes.byref(percent),
        ) != 0:
            return 1.0
        return percent.value / 100 if 100 <= percent.value <= 500 else 1.0
    except (AttributeError, OSError):
        return 1.0
