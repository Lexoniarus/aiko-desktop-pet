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
from typing import Callable, Iterable, Protocol, Sequence, cast


class Window(Protocol):
    """Only the tiny Tk window surface this module needs."""

    def winfo_exists(self) -> int: ...

    def winfo_ismapped(self) -> int: ...

    def winfo_id(self) -> int: ...


class NativeWindowOps(Protocol):
    def is_covered(self, root: Window, owned: Sequence[Window]) -> bool: ...

    def raise_without_focus(self, window: Window) -> bool: ...


class Win32WindowApi(Protocol):
    """Only Win32 calls used by Aiko, independently mockable in tests."""

    def GetAncestor(self, hwnd: int, flag: int) -> object: ...

    def GetWindow(self, hwnd: int, flag: int) -> object: ...

    def GetWindowRect(self, hwnd: int, rect_pointer: object) -> bool: ...

    def GetWindowLongW(self, hwnd: int, index: int) -> int: ...

    def IsWindowVisible(self, hwnd: int) -> bool: ...

    def IsIconic(self, hwnd: int) -> bool: ...

    def SetWindowPos(
        self, hwnd: int, after: int, x: int, y: int,
        width: int, height: int, flags: int,
    ) -> bool: ...


class _CtypesFunctionSignature(Protocol):
    """Writable ctypes function attributes used only at the FFI boundary."""

    argtypes: list[object]
    restype: object


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

    def __init__(self, user32: Win32WindowApi | None = None) -> None:
        if user32 is None:
            if sys.platform != "win32":
                raise RuntimeError("Win32 window management requires Windows")
            native_library = ctypes.WinDLL("user32", use_last_error=True)
            self._configure_win32_types(native_library)
            user32 = cast(Win32WindowApi, native_library)
        self.user32: Win32WindowApi = user32

    @staticmethod
    def _configure_win32_types(api: object) -> None:
        """Apply pointer-safe signatures to the dynamically loaded DLL."""
        # ctypes exposes DLL functions dynamically. The cast is isolated
        # here; application code accesses only the Win32WindowApi protocol.
        signatures: tuple[tuple[str, list[object], object], ...] = (
            ("GetAncestor", [wintypes.HWND, wintypes.UINT], wintypes.HWND),
            ("GetWindow", [wintypes.HWND, wintypes.UINT], wintypes.HWND),
            (
                "GetWindowRect", [wintypes.HWND, ctypes.POINTER(_Rect)],
                wintypes.BOOL,
            ),
            ("GetWindowLongW", [wintypes.HWND, ctypes.c_int], wintypes.LONG),
            ("IsWindowVisible", [wintypes.HWND], wintypes.BOOL),
            ("IsIconic", [wintypes.HWND], wintypes.BOOL),
            (
                "SetWindowPos",
                [
                    wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                    ctypes.c_int, ctypes.c_int, wintypes.UINT,
                ],
                wintypes.BOOL,
            ),
        )
        for name, argument_types, return_type in signatures:
            function = cast(_CtypesFunctionSignature, getattr(api, name))
            function.argtypes = argument_types
            function.restype = return_type

    @staticmethod
    def _handle(value: object) -> int:
        """Normalize Win32 handles returned as integers or ctypes pointers."""
        if isinstance(value, int):
            return value
        pointed_value = getattr(value, "value", None)
        return pointed_value if isinstance(pointed_value, int) else 0

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
        # ctypes structure fields are dynamic; bool() restores the declared
        # predicate type without changing Windows rectangle comparisons.
        return bool(
            a.left < b.right and b.left < a.right
            and a.top < b.bottom and b.top < a.bottom
        )

    def is_covered(self, root: Window, owned: Sequence[Window]) -> bool:
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
