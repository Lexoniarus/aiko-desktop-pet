"""Taskbar geometry is testable without Win32 or a GUI display."""

import unittest

from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.desktop.taskbar import ABE_BOTTOM, choose_track


class TaskbarTrackTests(unittest.TestCase):
    def test_bottom_docked_taskbar_sets_character_footline(self):
        track = choose_track(
            1920,
            1080,
            taskbar_rect=(0, 1032, 1920, 1080),
            taskbar_edge=ABE_BOTTOM,
            work_area=(0, 0, 1920, 1032),
        )
        self.assertEqual(track, TaskbarTrack(0, 1920, 1032))
        self.assertEqual(track.sprite_y(1), 838)
        self.assertEqual(track.sprite_y(2), 644)

    def test_non_default_taskbar_height_is_used(self):
        track = choose_track(
            2560, 1440, taskbar_rect=(0, 1361, 2560, 1440), taskbar_edge=3
        )
        self.assertEqual(track.ground_y, 1361)

    def test_taskbar_autohide_rect_does_not_reject_thin_rect(self):
        track = choose_track(
            1920, 1080, taskbar_rect=(0, 1078, 1920, 1080), taskbar_edge=3
        )
        self.assertEqual(track.ground_y, 1078)

    def test_off_axis_taskbar_prefers_usable_desktop(self):
        track = choose_track(
            1920,
            1080,
            taskbar_rect=(0, 0, 48, 1080),
            taskbar_edge=0,
            work_area=(48, 0, 1920, 1080),
        )
        self.assertEqual(track, TaskbarTrack(48, 1920, 1080))

    def test_missing_win32_geometry_uses_bottom_screen_fallback(self):
        self.assertEqual(choose_track(1366, 768), TaskbarTrack(0, 1366, 720))

    def test_invalid_taskbar_data_is_rejected(self):
        track = choose_track(
            1920,
            1080,
            taskbar_rect=(25, -900, 26, -400),
            taskbar_edge=3,
            work_area=(0, 0, 1920, 1045),
        )
        self.assertEqual(track.ground_y, 1045)

    def test_sprite_never_falls_off_horizontal_track(self):
        track = TaskbarTrack(48, 1920, 1032)
        self.assertEqual(track.clamp_x(-500, 128), 48)
        self.assertEqual(track.clamp_x(4000, 128), 1792)
        self.assertEqual(track.clamp_x(500, 128), 500)

    def test_unusually_small_screen_is_handled(self):
        track = choose_track(220, 180)
        self.assertEqual(track.sprite_y(2), 0)
        self.assertEqual(track.clamp_x(500, 256), 0)


if __name__ == "__main__":
    unittest.main()
