"""Read the usable Windows monitor at a point; no UI or pet state ownership."""

from __future__ import annotations

import sys

from ..ui.common.window_geometry import WindowBounds


def work_area_at(x: int, y: int, fallback: WindowBounds) -> WindowBounds:
    if sys.platform != "win32":
        return fallback

    import ctypes
    from ctypes import wintypes

    class MonitorInfo(ctypes.Structure):
        _fields_ = [
            ("size", wintypes.DWORD),
            ("monitor", wintypes.RECT),
            ("work", wintypes.RECT),
            ("flags", wintypes.DWORD),
        ]

    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
        user32.MonitorFromPoint.restype = wintypes.HANDLE
        user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MonitorInfo)]
        user32.GetMonitorInfoW.restype = wintypes.BOOL
        monitor = user32.MonitorFromPoint(wintypes.POINT(x, y), 2)
        info = MonitorInfo()
        info.size = ctypes.sizeof(MonitorInfo)
        if monitor and user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            rect = info.work
            if rect.right > rect.left and rect.bottom > rect.top:
                return WindowBounds(rect.left, rect.top, rect.right, rect.bottom)
    except (AttributeError, OSError):
        pass
    return fallback
