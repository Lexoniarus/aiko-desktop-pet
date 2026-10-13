"""Animated character tests that do not instantiate DesktopPet or HoverUi."""

from __future__ import annotations

import time
import tkinter as tk
import unittest
from unittest.mock import patch

from aiko_pet.personality.adaptive import AdaptiveRoutine
from aiko_pet.pet.state import PetState
from aiko_pet.application.settings import PetSettings
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.ui.animated_pet import AnimatedPet, AnimatedPorts


class IdleMonitor:
    def latest(self) -> ComputerSnapshot:
        return ComputerSnapshot(cpu=2)


class StandaloneAnimatedPetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            probe = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("No graphical display") from error
        probe.destroy()

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = tk.Canvas(self.root, width=128, height=208)
        self.canvas.pack()
        self.state = PetState()
        self.settings = PetSettings(x=100, y=500)
        self.cursor_samples: list[tuple[float, int, float]] = []
        self.anim = AnimatedPet(
            self.root, self.canvas,
            self.state, self.settings,
            AdaptiveRoutine(), IdleMonitor(),
            AnimatedPorts(
                track=lambda: TaskbarTrack(0, 800, 800),
                toolbar_visible=lambda: False,
                place_x=self._place_x,
                action_until=lambda: 0.0,
                action_state=lambda: "idle",
                walk_finished=lambda _now: None,
                cursor_moved=lambda distance, width, now: (
                    self.cursor_samples.append((distance, width, now))
                ),
            ),
        )
        self.addCleanup(self.root.destroy)

    def _place_x(self, value: float) -> None:
        self.settings.x = round(value)

    def test_sprites_and_gaze_do_not_require_hover_ui(self) -> None:
        self.assertFalse(hasattr(self.anim, "pet"))
        self.assertEqual(self.anim.sprites["idle"][0].width(), 128)
        self.anim.show_frame("idle", time.monotonic(), fixed=0)
        self.settings.follow_cursor = False
        self.assertIsNone(self.anim.gaze_direction((10000, 0)))

    def test_movement_uses_injected_geometry_boundary(self) -> None:
        self.anim.movement.remaining_distance = 12
        result = self.anim.maybe_walk(time.monotonic() + 1000, 0.25)
        self.assertEqual(result, "running-right")
        assert self.settings.x is not None
        self.assertGreater(self.settings.x, 100)
        self.assertEqual(self.anim.movement.remaining_distance, 0)

    def test_cursor_motion_emits_observation_without_dialogue_policy(self) -> None:
        with (
            patch.object(self.root, "winfo_pointerx", side_effect=[10, 99999]),
            patch.object(self.root, "winfo_pointery", side_effect=[20, -99999]),
        ):
            self.anim.observe_pointer(900.0)
            self.anim.observe_pointer(1000.0)
        self.assertEqual(len(self.cursor_samples), 1)
        distance, width, now = self.cursor_samples[0]
        self.assertGreater(distance, width * 0.6)
        self.assertEqual(now, 1000.0)
        self.assertEqual(self.anim.last_pointer_move, 1000.0)

    def test_visual_settings_are_owned_by_animated_character(self) -> None:
        self.anim.movement.remaining_distance = 30
        self.anim.set_auto_walk(False, now=500)
        self.assertFalse(self.settings.auto_walk)
        self.assertEqual(self.anim.movement.remaining_distance, 0)
        self.assertGreater(self.anim.movement.next_walk_at, 500)
        self.anim.gaze_sector = 3
        self.anim.set_follow_cursor(False)
        self.assertFalse(self.settings.follow_cursor)
        self.assertIsNone(self.anim.gaze_sector)

    def test_scale_reload_keeps_frame_identity(self) -> None:
        self.settings.scale = 2
        self.anim.reload_sprites()
        self.assertEqual(self.anim.sprites["idle"][0].width(), 256)


if __name__ == "__main__":
    unittest.main()
