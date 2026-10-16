"""Native resting-item hit testing without sending clicks to the user's desktop."""

import ctypes
import sys
import tkinter as tk
import unittest
from ctypes import wintypes

from aiko_pet.desktop.window_stack import WindowsWindowOps
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.ui.world_view import WorldView
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    WorldSurface,
)
from aiko_pet.world.state import WorldState


@unittest.skipUnless(sys.platform == "win32", "Windows layered-window hit testing")
class ObjectWindowTests(unittest.TestCase):
    def test_visible_pixels_accept_input_without_activating_and_motion_is_passive(self):
        root = tk.Tk()
        self.addCleanup(root.destroy)
        root.geometry("240x220+100+100")
        root.configure(bg="blue")
        root.update()
        view = WorldView(root, load_item_catalog())
        self.addCleanup(view.close)
        world = WorldState(WorldSurface(800, 600),
                           (ObjectDefinition("apple", "apple"),))
        item = world.place_resting("apple", 160, ObjectFootprint(8, 8))
        ops = WindowsWindowOps()
        api = ctypes.WinDLL("user32")
        api.GetForegroundWindow.restype = wintypes.HWND
        api.WindowFromPoint.argtypes = [wintypes.POINT]
        api.WindowFromPoint.restype = wintypes.HWND
        foreground = api.GetForegroundWindow()
        for scale in (1, 2):
            with self.subTest(scale=scale):
                view.sync(world.snapshot(), left=0, ground_y=190,
                          scale=scale, topmost=True)
                root.update()
                entry = view._windows[item.instance_id]
                hwnd = ops.hwnd(entry.window)
                self.assertEqual(api.GetForegroundWindow(), foreground)
                style = ops.user32.GetWindowLongW(hwnd, -20)
                self.assertTrue(style & 0x08000000)
                self.assertFalse(style & 0x20)
                image = view.image("apple", scale)
                opaque = next((x, y) for y in range(image.height())
                              for x in range(image.width())
                              if not image.transparency_get(x, y)
                              and image.get(x, y) != (255, 0, 255))
                clear = next((x, y) for y in range(image.height())
                             for x in range(image.width())
                             if image.transparency_get(x, y)
                             or image.get(x, y) == (255, 0, 255))

                def window_at(pixel):
                    point = wintypes.POINT(entry.window.winfo_rootx() + pixel[0],
                                           entry.window.winfo_rooty() + pixel[1])
                    hit = api.WindowFromPoint(point)
                    return ops._handle(ops.user32.GetAncestor(hit, 2))

                self.assertEqual(window_at(opaque), hwnd)
                self.assertNotEqual(window_at(clear), hwnd)
        held = world.take_resting(item.instance_id, expected_revision=0)
        world.release(item.instance_id, expected_revision=held.revision)
        view.sync(world.snapshot(), left=0, ground_y=190, scale=2, topmost=True)
        root.update()
        self.assertTrue(ops.user32.GetWindowLongW(hwnd, -20) & 0x20)
