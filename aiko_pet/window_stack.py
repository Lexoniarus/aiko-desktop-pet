"""Centralized, non-activating z-order management for Aiko's Tk windows.

Tk represents the sprite, toolbar and speech bubble as separate native windows.
A browser popup can outrank one of these windows while another remains above it.
On Windows, repair that mismatch only when a foreign, visible window actually
covers the sprite, rather than calling ``lift`` on every 140 ms animation tick.
"""

from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from typing import Callable, Iterable, Protocol


class Window(Protocol):
    """Only the tiny Tk window surface this module needs."""

    def winfo_exists(self) -> int: ...

    def winfo_ismapped(self) -> int: ...

    def winfo_id(self) -> int: ...


class NativeWindowOps(Protocol):
    def is_covered(self, root: Window, owned: list[Window]) -> bool: ...

    def raise_without_focus(self, window: Window) -> bool: ...


class _Rect(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class WindowsWindowOps:
    """Win32 API bridge; Tk's window id may refer to an inner HWND."""

    GA_ROOT = 2
    GW_HWNDPREV = 3
    GWL_EXSTYLE = -20
    WS_EX_TOPMOST = 0x00000008
    HWND_TOPMOST = -1
    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_NOACTIVATE = 0x0010
    SWP_NOOWNERZORDER = 0x0200
    MOVE_FLAGS = SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_NOOWNERZORDER

    def __init__(self, user32: object | None = None) -> None:
        if user32 is None:
            if sys.platform != "win32":
                raise RuntimeError("Win32 window management requires Windows")
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            self._configure_win32_types(user32)
        self.user32 = user32

    @staticmethod
    def _configure_win32_types(api: object) -> None:
        # Explicit pointer types are essential for 64-bit HWND values.
        api.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        api.GetAncestor.restype = wintypes.HWND
        api.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
        api.GetWindow.restype = wintypes.HWND
        api.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(_Rect)]
        api.GetWindowRect.restype = wintypes.BOOL
        api.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
        api.GetWindowLongW.restype = wintypes.LONG
        api.IsWindowVisible.argtypes = [wintypes.HWND]
        api.IsWindowVisible.restype = wintypes.BOOL
        api.IsIconic.argtypes = [wintypes.HWND]
        api.IsIconic.restype = wintypes.BOOL
        api.SetWindowPos.argtypes = [
            wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, wintypes.UINT,
        ]
        api.SetWindowPos.restype = wintypes.BOOL

    @staticmethod
    def _handle(value: object) -> int:
        return int(getattr(value, "value", value) or 0)

    def hwnd(self, window: Window) -> int:
        if not window.winfo_exists():
            return 0
        inner = int(window.winfo_id())
        return self._handle(self.user32.GetAncestor(inner, self.GA_ROOT)) or inner

    def _rect(self, hwnd: int) -> _Rect | None:
        rect = _Rect()
        if self.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return rect
        return None

    @staticmethod
    def _overlaps(a: _Rect, b: _Rect) -> bool:
        return (
            a.left < b.right and b.left < a.right
            and a.top < b.bottom and b.top < a.bottom
        )

    def is_covered(self, root: Window, owned: list[Window]) -> bool:
        """True if a *foreign* visible overlapping window outranks the sprite.

        Ignore our other Tk windows (notably the speech bubble). The topmost
        style alone is insufficient: two topmost windows can be reordered.
        """
        sprite = self.hwnd(root)
        if not sprite:
            return False
        style = self.user32.GetWindowLongW(sprite, self.GWL_EXSTYLE)
        if not (style & self.WS_EX_TOPMOST):
            return True
        sprite_rect = self._rect(sprite)
        if sprite_rect is None:
            return False
        own_handles = {self.hwnd(window) for window in owned}
        own_handles.add(sprite)
        seen: set[int] = set()
        current = self._handle(self.user32.GetWindow(sprite, self.GW_HWNDPREV))
        # Do not loop indefinitely if Windows returns malformed z-order data.
        for _ in range(512):
            if not current or current in seen:
                break
            seen.add(current)
            if (
                current not in own_handles
                and self.user32.IsWindowVisible(current)
                and not self.user32.IsIconic(current)
            ):
                other = self._rect(current)
                if other is not None and self._overlaps(sprite_rect, other):
                    return True
            current = self._handle(self.user32.GetWindow(current, self.GW_HWNDPREV))
        return False

    def raise_without_focus(self, window: Window) -> bool:
        """Reassert topmost z-order without activating or focusing the app."""
        hwnd = self.hwnd(window)
        if not hwnd:
            return False
        return bool(self.user32.SetWindowPos(
            hwnd, self.HWND_TOPMOST, 0, 0, 0, 0, self.MOVE_FLAGS,
        ))


class WindowStack:
    """Own the order of all visible Aiko windows in one place.

    ``maintain`` is a low-frequency *conditional* check. ``restore`` is for
    known UI transitions (e.g. showing a bubble). Both never request focus.
    """

    def __init__(
        self,
        windows: Callable[[], Iterable[Window]],
        *,
        enabled: bool,
        backend: NativeWindowOps | None = None,
    ) -> None:
        self._windows = windows
        self.enabled = bool(enabled)
        self._last_maintenance_repair = float("-inf")
        self._backend = (
            backend if backend is not None else
            (WindowsWindowOps() if sys.platform == "win32" else None)
        )

    def restore(self) -> bool:
        if not self.enabled or self._backend is None:
            return False
        visible = [
            window for window in self._windows()
            if window.winfo_exists() and window.winfo_ismapped()
        ]
        if not visible:
            return False
        # Raise back-to-front: sprite first, its tool windows afterwards.
        results = [self._backend.raise_without_focus(window) for window in visible]
        return all(results)

    def maintain(self) -> bool:
        if not self.enabled or self._backend is None:
            return False
        # Avoid fighting a different application's intentionally topmost UI.
        now = time.monotonic()
        if now - self._last_maintenance_repair < 3.0:
            return False
        visible = [
            window for window in self._windows()
            if window.winfo_exists() and window.winfo_ismapped()
        ]
        if not visible or not self._backend.is_covered(visible[0], visible):
            return False
        self._last_maintenance_repair = now
        self.restore()
        return True
