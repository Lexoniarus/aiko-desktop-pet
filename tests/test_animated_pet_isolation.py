"""Animated character tests that do not instantiate DesktopPet or HoverUi."""

from __future__ import annotations

import time
import tkinter as tk
import unittest
from unittest.mock import patch

from aiko_pet.adaptive import AdaptiveRoutine
from aiko_pet.domain import PetState
from aiko_pet.storage import PetSettings
from aiko_pet.system_activity import ComputerSnapshot
from aiko_pet.taskbar import TaskbarTrack
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
        self.cursor_events: list[str] = []
        self.anim = AnimatedPet(
            self.root, self.canvas,
            self.state, self.settings,
            AdaptiveRoutine(), IdleMonitor(),
            AnimatedPorts(
                track=lambda: TaskbarTrack(0, 800, 800),
                toolbar_visible=lambda: False,
                place_x=self._place_x,
                last_spoken=lambda: -1000.0,
                action_until=lambda: 0.0,
                action_state=lambda: "idle",
                walk_pause=lambda _now: None,
                cursor_reaction=lambda event, _now: (
                    self.cursor_events.append(event)
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

    def test_cursor_attention_only_emits_an_event(self) -> None:
        self.anim.next_cursor_line = 0
        with (
            patch.object(self.root, "winfo_pointerx", side_effect=[10, 99999]),
            patch.object(self.root, "winfo_pointery", side_effect=[20, -99999]),
            patch("aiko_pet.ui.animated_pet.random.random", return_value=0.01),
        ):
            self.anim.observe_pointer(900.0)
            self.anim.observe_pointer(1000.0)
        self.assertEqual(self.cursor_events, ["cursor_far"])
        self.assertEqual(self.anim.last_pointer_move, 1000.0)

    def test_scale_reload_keeps_frame_identity(self) -> None:
        self.settings.scale = 2
        self.anim.reload_sprites()
        self.assertEqual(self.anim.sprites["idle"][0].width(), 256)


if __name__ == "__main__":
    unittest.main()
