"""Native passive object windows, isolated from Tk rendering and pet rules."""

import ctypes
import sys
from ctypes import wintypes

from .window_stack import Window, WindowsWindowOps


def make_object_window_passive(window: Window) -> None:
    if sys.platform != "win32":
        return
    ops = WindowsWindowOps()
    hwnd = ops.hwnd(window)
    api = ctypes.windll.user32
    setter = api.SetWindowLongW
    setter.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
    setter.restype = wintypes.LONG
    style = ops.user32.GetWindowLongW(hwnd, -20)
    setter(hwnd, -20, style | 0x08000000 | 0x00000020)
    ops.raise_without_focus(window)
