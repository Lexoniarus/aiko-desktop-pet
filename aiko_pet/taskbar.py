"""Horizontal walking track along the primary Windows taskbar.

On Windows the actual bottom-docked taskbar is queried via SHAppBarMessage.
The primary monitor's work area is the fallback.  The geometry calculations
are independent of Tkinter and can be unit-tested without a display.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

# In the prepared 128x208 sprites the characters' lowest opaque row is 193.
# Positioning this baseline at the upper taskbar edge makes Aiko stand on it.
FOOT_BASELINE = 194
FALLBACK_TASKBAR_HEIGHT = 48
ABE_BOTTOM = 3


@dataclass(frozen=True)
class TaskbarTrack:
    """Primary-monitor horizontal route; coordinates are screen pixels."""

    left: int
    right: int
    ground_y: int

    def clamp_x(self, x: float, sprite_width: int) -> int:
        """Keep the full sprite window horizontally inside the walking track."""
        maximum = max(self.left, self.right - sprite_width)
        return max(self.left, min(round(x), maximum))

    def sprite_y(self, scale: int) -> int:
        """Place the sprite's feet at the taskbar, not its transparent margin."""
        return max(0, self.ground_y - FOOT_BASELINE * scale)


def choose_track(
    screen_width: int,
    screen_height: int,
    *,
    taskbar_rect: tuple[int, int, int, int] | None = None,
    taskbar_edge: int | None = None,
    work_area: tuple[int, int, int, int] | None = None,
) -> TaskbarTrack:
    """Select a safe, horizontal route on the primary screen.

    The default is deliberately bottom-aligned. When a taskbar isn't docked
    at the bottom (or its location is unavailable), Aiko walks on the lower
    edge of the usable desktop instead of crossing the application area.
    """
    width = max(1, screen_width)
    height = max(1, screen_height)

    if taskbar_rect is not None and taskbar_edge == ABE_BOTTOM:
        left, top, right, bottom = taskbar_rect
        clipped_left = max(0, left)
        clipped_right = min(width, right)
        # Reject tiny/incoherent rectangles but permit thin auto-hide bars.
        if (
            clipped_right - clipped_left >= width // 2
            and bottom > top
            and height // 3 <= top <= height
        ):
            return TaskbarTrack(clipped_left, clipped_right, top)

    if work_area is not None:
        left, top, right, bottom = work_area
        clipped_left = max(0, left)
        clipped_right = min(width, right)
        clipped_bottom = min(height, bottom)
        if (
            clipped_right > clipped_left
            and top >= 0
            and clipped_bottom > top
            and clipped_bottom >= height // 3
        ):
            return TaskbarTrack(clipped_left, clipped_right, clipped_bottom)

    return TaskbarTrack(0, width, max(0, height - FALLBACK_TASKBAR_HEIGHT))


def _windows_desktop_geometry() -> tuple[
    tuple[int, int, int, int] | None,
    int | None,
    tuple[int, int, int, int] | None,
]:
    """Read taskbar/work-area data using Win32, with graceful fallback."""
    if sys.platform != "win32":
        return None, None, None

    import ctypes
    from ctypes import wintypes

    class AppBarData(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("hWnd", wintypes.HWND),
            ("uCallbackMessage", wintypes.UINT),
            ("uEdge", wintypes.UINT),
            ("rc", wintypes.RECT),
            ("lParam", ctypes.c_ssize_t),
        ]

    taskbar_rect = None
    taskbar_edge = None
    work_area = None
    try:
        shell = ctypes.WinDLL("shell32", use_last_error=True)
        shell.SHAppBarMessage.argtypes = [wintypes.DWORD, ctypes.POINTER(AppBarData)]
        shell.SHAppBarMessage.restype = ctypes.c_size_t
        bar = AppBarData()
        bar.cbSize = ctypes.sizeof(AppBarData)
        if shell.SHAppBarMessage(5, ctypes.byref(bar)):  # ABM_GETTASKBARPOS
            rect = bar.rc
            taskbar_rect = (rect.left, rect.top, rect.right, rect.bottom)
            taskbar_edge = bar.uEdge
    except (AttributeError, OSError):
        pass

    try:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.SystemParametersInfoW.argtypes = [
            wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT,
        ]
        user32.SystemParametersInfoW.restype = wintypes.BOOL
        rect = wintypes.RECT()
        if user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            work_area = (rect.left, rect.top, rect.right, rect.bottom)
    except (AttributeError, OSError):
        pass
    return taskbar_rect, taskbar_edge, work_area


def locate_primary_taskbar(screen_width: int, screen_height: int) -> TaskbarTrack:
    """Return the primary monitor's track with no extra runtime packages."""
    bar, edge, work_area = _windows_desktop_geometry()
    return choose_track(
        screen_width,
        screen_height,
        taskbar_rect=bar,
        taskbar_edge=edge,
        work_area=work_area,
    )
