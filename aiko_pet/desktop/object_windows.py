"""Native passive object windows, isolated from Tk rendering and pet rules."""

import ctypes
import sys
from ctypes import wintypes

from .window_stack import Window, WindowsWindowOps


def configure_object_window(
    window: Window, *, interactive: bool = False,
    x: int | None = None, y: int | None = None,
) -> None:
    if sys.platform != "win32":
        return
    ops = WindowsWindowOps()
    hwnd = ops.hwnd(window)
    api = ctypes.windll.user32
    setter = api.SetWindowLongW
    setter.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
    setter.restype = wintypes.LONG
    style = ops.user32.GetWindowLongW(hwnd, -20)
    # Windows already hit-tests color-keyed layered windows per visible pixel.
    # WS_EX_TRANSPARENT bypasses that shape entirely for moving/carried items.
    style = style | 0x08000000
    style = style & ~0x00000020 if interactive else style | 0x00000020
    setter(hwnd, -20, style)
    if x is not None and y is not None:
        ops.user32.SetWindowPos(hwnd, 0, x, y, 0, 0,
                               0x0001 | 0x0004 | 0x0010 | 0x0200)
    ops.raise_without_focus(window)
