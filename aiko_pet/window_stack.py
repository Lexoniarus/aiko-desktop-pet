"""Legacy native-window imports, implemented by desktop.window_stack."""

from __future__ import annotations

import ctypes as ctypes
import sys as sys
import time as time

from .desktop.window_stack import (
    Window as Window,
    NativeWindowOps as NativeWindowOps,
    Win32WindowApi as Win32WindowApi,
    _CtypesFunctionSignature as _CtypesFunctionSignature,
    _Rect as _Rect,
    WindowsWindowOps as WindowsWindowOps,
    WindowStack as WindowStack,
)
