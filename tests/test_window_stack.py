"""Non-activating overlay policy, including simulated Win32 z-order changes."""

import ctypes
import unittest

from aiko_pet.desktop.window_stack import WindowStack, WindowsWindowOps, _Rect


class WindowStub:
    def __init__(self, hwnd, *, mapped=True):
        self.id = hwnd
        self.mapped = mapped

    def winfo_exists(self):
        return 1

    def winfo_ismapped(self):
        return int(self.mapped)

    def winfo_id(self):
        return self.id


class WindowsStub:
    """Simulate a browser popup outranking Tk's own windows."""

    def __init__(self):
        self.parents = {101: 201, 102: 202, 103: 203}
        # Starting at sprite (201), bubble (202) and browser popup (300)
        # are above it; browser popup is a foreign window.
        self.above = {201: 202, 202: 300, 300: 0}
        self.rects = {
            201: (400, 580, 528, 788),
            202: (415, 525, 600, 580),
            203: (530, 580, 880, 788),
            300: (0, 0, 1920, 1080),
        }
        self.visible = {201, 202, 203, 300}
        self.styles = {201: 0x8}
        self.calls = []

    def GetAncestor(self, hwnd, _flag):
        return self.parents.get(hwnd, hwnd)

    def GetWindow(self, hwnd, _flag):
        return self.above.get(hwnd, 0)

    def GetWindowRect(self, hwnd, rect):
        bounds = self.rects.get(hwnd)
        if bounds is None:
            return False
        out = ctypes.cast(rect, ctypes.POINTER(_Rect)).contents
        out.left, out.top, out.right, out.bottom = bounds
        return True

    def GetWindowLongW(self, hwnd, _field):
        return self.styles.get(hwnd, 0)

    def IsWindowVisible(self, hwnd):
        return hwnd in self.visible

    def IsIconic(self, _hwnd):
        return False

    def SetWindowPos(self, hwnd, target, x, y, width, height, flags):
        self.calls.append((hwnd, target, x, y, width, height, flags))
        return True


class WindowStackUnitTests(unittest.TestCase):
    def setUp(self):
        self.user32 = WindowsStub()
        self.api = WindowsWindowOps(self.user32)
        self.pet = WindowStub(101)
        self.bubble = WindowStub(102)
        self.toolbar = WindowStub(103)
        self.windows = [self.pet, self.toolbar, self.bubble]
        self.stack = WindowStack(lambda: self.windows, enabled=True, backend=self.api)

    def test_foreign_browser_popup_outranks_aiko_and_triggers_repair(self):
        self.assertTrue(self.api.is_covered(self.pet, self.windows))
        self.assertTrue(self.stack.maintain())
        self.assertEqual([call[0] for call in self.user32.calls], [201, 203, 202])
        for hwnd, target, x, y, width, height, flags in self.user32.calls:
            self.assertEqual(target, WindowsWindowOps.HWND_TOPMOST)
            self.assertEqual((x, y, width, height), (0, 0, 0, 0))
            self.assertEqual(flags, WindowsWindowOps.MOVE_FLAGS)
            self.assertTrue(flags & WindowsWindowOps.SWP_NOACTIVATE)

    def test_our_own_speech_bubble_does_not_trigger_repair(self):
        self.user32.above = {201: 202, 202: 0}
        self.assertFalse(self.api.is_covered(self.pet, self.windows))
        self.assertFalse(self.stack.maintain())
        self.assertEqual(self.user32.calls, [])

    def test_unrelated_non_overlapping_window_does_not_trigger_repair(self):
        self.user32.rects[300] = (1000, 80, 1500, 400)
        self.assertFalse(self.stack.maintain())
        self.assertEqual(self.user32.calls, [])

    def test_windows_that_are_not_visible_or_minimized_do_not_count(self):
        self.user32.visible.remove(300)
        self.assertFalse(self.stack.maintain())

    def test_root_without_topmost_style_is_repaired(self):
        self.user32.styles[201] = 0
        self.user32.above = {201: 0}
        self.assertTrue(self.stack.maintain())

    def test_disabled_mode_does_not_interfere_with_other_apps(self):
        self.stack.enabled = False
        self.assertFalse(self.stack.maintain())
        self.assertFalse(self.stack.restore())
        self.assertEqual(self.user32.calls, [])

    def test_hidden_windows_are_not_raised(self):
        self.toolbar.mapped = False
        self.assertTrue(self.stack.restore())
        self.assertEqual([call[0] for call in self.user32.calls], [201, 202])

    def test_native_handle_normalization_accepts_ctypes_pointer(self):
        self.assertEqual(self.api._handle(ctypes.c_void_p(123)), 123)
        self.assertEqual(self.api._handle(None), 0)
        self.assertEqual(self.api._handle(ctypes.c_void_p(None)), 0)

    def test_hwnd_resolution_uses_top_level_wrapper_not_inner_tk_handle(self):
        self.assertEqual(self.api.hwnd(self.pet), 201)

    def test_no_restoration_when_z_order_is_healthy(self):
        self.user32.above = {201: 202, 202: 0}
        self.assertFalse(self.stack.maintain())
        self.assertEqual(self.user32.calls, [])


    def test_maintenance_is_rate_limited(self):
        # A browser may insist on keeping its own topmost dialog in front;
        # never fight it on every 140 ms animation tick.
        from unittest.mock import patch

        with patch("aiko_pet.desktop.window_stack.time.monotonic", side_effect=[12, 13, 17]):
            self.assertTrue(self.stack.maintain())
            count = len(self.user32.calls)
            self.assertFalse(self.stack.maintain())
            self.assertEqual(len(self.user32.calls), count)
            self.assertTrue(self.stack.maintain())
            self.assertEqual(len(self.user32.calls), count + 3)


if __name__ == "__main__":
    unittest.main()
