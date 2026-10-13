"""Animated character tests that do not instantiate DesktopPet or HoverUi."""

from __future__ import annotations

import time
import tkinter as tk
import unittest
from unittest.mock import patch

from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.personality.adaptive import AdaptiveRoutine
from aiko_pet.pet.state import PetState
from aiko_pet.application.settings import PetSettings
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.presentation.movement import WalkController
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
        self.canvas = tk.Canvas(self.root, width=192, height=208)
        self.canvas.pack()
        self.state = PetState()
        self.settings = PetSettings(x=100, y=500)
        self.cursor_samples: list[tuple[float, int, float]] = []
        self.action_deadlines: list[float] = []
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
                extend_action=self.action_deadlines.append,
            ),
            assets=load_character_catalog(),
        )
        self.addCleanup(self.root.destroy)
        self.addCleanup(self.anim.stop)

    def _place_x(self, value: float) -> None:
        self.settings.x = round(value)

    def test_sprites_and_gaze_do_not_require_hover_ui(self) -> None:
        self.assertFalse(hasattr(self.anim, "pet"))
        self.assertEqual(self.anim.sprites["idle"][0].width(), 192)
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

    def test_short_frames_advance_without_a_desktop_simulation_tick(self) -> None:
        self.anim.begin_action("waving", time.monotonic())
        self.root.after(195, self.root.quit)
        self.root.mainloop()
        self.assertEqual(self.anim.frame_clock.active_key, ("waving", None))
        self.assertGreaterEqual(self.anim.frame_clock.frame_index, 1)

    def test_sleep_plays_the_full_width_breathing_clip(self) -> None:
        self.state.sleeping = True
        now = time.monotonic()
        self.anim.render(now, 0, (0, 0))
        self.assertEqual(self.anim.frame_clock.active_key, ("sleep", None))
        self.anim.show_frame("sleep", now + .5)
        self.assertEqual(self.anim.frame_clock.frame_index, 1)
        self.assertEqual(self.anim.sprites["sleep"][0].width(), 192)

    def test_one_shot_returns_to_idle_and_ignores_cancelled_callbacks(self) -> None:
        now = time.monotonic()
        self.anim.begin_action("petting", now)
        old_generation = self.anim._frame_generation
        self.anim.begin_action("eat", now + .1)
        initial_deadline = self.action_deadlines[-1]
        self.anim._advance_frame("petting", None, old_generation)
        self.assertEqual(self.anim.frame_clock.active_key, ("eat", None))
        for frame in self.anim.assets.clips["eat"].frames:
            shown_at = self.anim.frame_clock.frame_started_at
            self.anim.show_frame("eat", shown_at + frame.duration_ms / 1000 + .01)
        self.assertEqual(self.anim.frame_clock.active_key, ("idle", None))
        self.assertGreater(self.action_deadlines[-1], initial_deadline)
        self.anim.stop()
        self.assertIsNone(self.anim._frame_timer)

    def test_walking_moves_between_desktop_ticks(self) -> None:
        self.settings.follow_cursor = False
        self.anim.movement.remaining_distance = 100
        now = time.monotonic()
        self.anim.render(now, .14, (0, 0))
        self.assertEqual(self.settings.x, 100)
        self.root.after(105, self.root.quit)
        self.root.mainloop()
        assert self.settings.x is not None
        self.assertGreater(self.settings.x, 100)
        self.assertLess(self.settings.x, 108)
        self.assertEqual(self.anim.frame_clock.active_key, ("running-right", None))

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

    def test_late_frames_still_move_one_stride_per_cycle_at_both_sizes(self) -> None:
        for scale in (1, 2):
            for direction, name in ((1, 'running-right'), (-1, 'running-left')):
                with self.subTest(scale=scale, direction=direction):
                    self.settings.scale = scale
                    self.settings.x = 100 if direction > 0 else 400
                    start_x = self.settings.x
                    self.anim.reload_sprites()
                    now = time.monotonic()
                    self.anim.movement = WalkController(next_walk_at=now + 100)
                    self.anim.movement.remaining_distance = 1000 * direction
                    self.anim.frame_clock.reset()
                    self.anim.show_frame(name, now)
                    frames = [0]
                    for duration in self.anim.assets.clips[name].timings:
                        now = self.anim.frame_clock.frame_started_at + duration / 1000 + .1
                        # Simulate Tk consuming the scheduled callback first.
                        assert self.anim._frame_timer is not None
                        self.root.after_cancel(self.anim._frame_timer)
                        with patch('aiko_pet.ui.animated_pet.time.monotonic',
                                   return_value=now):
                            self.anim._advance_frame(name, None,
                                                     self.anim._frame_generation)
                        frames.append(self.anim.frame_clock.frame_index)
                    self.assertEqual(frames, list(range(8)) + [0])
                    self.assertEqual(self.settings.x, start_x + 68 * scale * direction)

    def test_game_mode_freezes_cursor_gaze_and_uses_existing_pose(self) -> None:
        self.anim.set_game_mode(True)
        self.assertIsNone(self.anim.gaze_direction((99999, -99999)))
        self.assertIsNone(self.anim.maybe_walk(time.monotonic(), 0.3))
        self.anim.observe_pointer(time.monotonic())
        self.assertIsNone(self.anim.gaze_sector)
        self.anim.render(time.monotonic(), .14, (99999, -99999))
        self.assertEqual(self.anim.frame_clock.active_key, ("waiting", None))
        self.anim.begin_action("jumping", time.monotonic())
        self.anim.render(time.monotonic(), .14, (99999, -99999))
        self.assertEqual(self.anim.frame_clock.active_key, ("jumping", None))
        self.anim.set_game_mode(False)
        self.assertNotEqual(self.anim.frame_clock.active_key, ("jumping", None))
        self.assertIsNotNone(self.anim.gaze_direction((99999, -99999)))

    def test_idle_blinks_once_then_holds_a_neutral_pose(self) -> None:
        self.settings.auto_walk = False
        self.settings.observe_computer = False
        self.settings.follow_cursor = False
        now = time.monotonic()
        self.anim._ambient.next_blink_at = now - 1
        self.anim._ambient.next_glance_at = now + 200
        self.anim.render(now, 0, (0, 0))
        self.assertTrue(self.anim._ambient.blinking)
        self.assertEqual(self.anim.frame_clock.active_key, ("idle", None))
        observed = [self.anim.frame_clock.frame_index]
        for _ in range(8):
            elapsed = self.anim.assets.clips["idle"].timings[0] / 1000
            step = self.anim.frame_clock.frame_started_at + elapsed + .001
            self.anim.show_frame("idle", step)
            if self.anim._ambient.blinking:
                observed.append(self.anim.frame_clock.frame_index)
        self.assertEqual(observed, list(range(8)))
        self.assertFalse(self.anim._ambient.blinking)
        self.assertEqual(self.anim.frame_clock.active_key, ("idle", 0))
        self.assertIsNone(self.anim._frame_timer)
        self.anim.render(now + 2.0, 0, (0, 0))
        self.assertEqual(self.anim.frame_clock.active_key, ("idle", 0))

    def test_aiko_looks_around_even_when_the_pointer_stays_still(self) -> None:
        self.settings.auto_walk = False
        self.settings.observe_computer = False
        now = time.monotonic()
        self.anim._ambient.next_blink_at = now + 200
        self.anim._ambient.next_glance_at = now - 1
        self.anim.render(now, 0, (0, 0))
        active = self.anim.frame_clock.active_key
        assert active is not None
        self.assertEqual(active[0], "look")
        self.assertIn(active[1], (2, 3, 4, 12, 13, 14))
        self.assertIsNone(self.anim._frame_timer)
        self.anim.render(self.anim._ambient._glance_until + .1, 0, (0, 0))
        self.assertEqual(self.anim.frame_clock.active_key, ("idle", 0))

    def test_spontaneous_glance_never_overrides_sleep_or_game(self) -> None:
        now = time.monotonic()
        self.anim.set_game_mode(True)
        self.anim._ambient.next_glance_at = now - 1
        self.anim.render(now, 0, (0, 0))
        self.assertEqual(self.anim.frame_clock.active_key, ("waiting", None))
        self.anim.set_game_mode(False)
        self.state.sleeping = True
        self.anim._ambient.next_glance_at = now - 1
        self.anim.render(now + 1, 0, (0, 0))
        self.assertEqual(self.anim.frame_clock.active_key, ("sleep", None))

    def test_scale_reload_keeps_frame_identity(self) -> None:
        self.settings.scale = 2
        self.anim.reload_sprites()
        self.assertEqual(self.anim.sprites["idle"][0].width(), 384)


if __name__ == "__main__":
    unittest.main()
