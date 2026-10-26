"""Animated character tests that do not instantiate DesktopPet or HoverUi."""

from __future__ import annotations

import time
import tkinter as tk
import unittest
from unittest.mock import patch

from aiko_pet.application.settings import PetSettings
from aiko_pet.desktop.animation_runtime import (
    AnimationRuntimePorts,
    DesktopAnimationRuntime,
)
from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.desktop.visual_observation import DesktopVisualObservation
from aiko_pet.desktop.walk_runtime import WalkDriver, WalkDriverPorts
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.pet.animation.character import FRAME_WIDTH
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.cursor_attention import CursorAttentionSnapshot
from aiko_pet.pet.movement import WalkController
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.pet_view.animated_pet import AnimatedPet, AnimatedPorts
from tools.pet_test_support import set_test_pet_values


class IdleMonitor:
    def latest(self) -> ComputerSnapshot:
        return ComputerSnapshot(cpu=2)


class StandaloneAnimatedPetTests(unittest.TestCase):
    def test_step_head_change_keeps_playback_progress(self) -> None:
        now = time.monotonic()
        self.anim.show_frame("body-step-right-02", now)
        self.anim.show_frame("body-step-right-02", now + .08)
        index = self.anim.frame_clock.frame_index
        self.anim.show_frame("body-step-right-06", now + .09)
        self.assertEqual(self.anim.frame_clock.frame_index, index)
        self.assertEqual(self.anim.frame_clock.active_key, ("body-step-right", None))

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
        self.action_deadlines: list[float] = []
        assets = load_character_catalog()
        self.walk = WalkDriver(
            state=self.state,
            settings=self.settings,
            adaptive=AdaptiveRoutine(),
            monitor=IdleMonitor(),
            walk_cycle_seconds=assets.clips["running-left"].duration_seconds,
            ports=WalkDriverPorts(
                track=lambda: TaskbarTrack(0, 800, 800),
                menu_engaged=lambda: False,
                place_x=self._place_x,
                walk_finished=lambda _now: None,
            ),
        )
        self.visual = DesktopVisualObservation(
            settings=self.settings,
            monitor=IdleMonitor(),
            eyes=lambda: (
                self.root.winfo_x() + (FRAME_WIDTH // 2) * self.settings.scale,
                self.root.winfo_y() + 82 * self.settings.scale,
            ),
        )
        self.animation = DesktopAnimationRuntime(
            state=self.state,
            settings=self.settings,
            assets=assets,
            walk=self.walk,
            visual=self.visual,
            ports=AnimationRuntimePorts(
                action_until=lambda: 0.0,
                action_clip_id=lambda: "idle",
                attention_until=lambda: self.anim._cursor_snapshot.attention_until,
            ),
        )
        self.anim = AnimatedPet(
            self.root,
            self.canvas,
            self.state,
            self.settings,
            AnimatedPorts(
                walk_step=self._step_walk,
                walk_active=self.animation.walk_active,
                interrupt_walk=self.animation.interrupt_walk,
                choose_animation=self.animation.select_animation,
                reset_gaze=self.visual.reset,
                extend_action=self.action_deadlines.append,
            ),
            assets=assets,
            items=load_item_catalog(),
            ambient=self.animation.ambient,
        )
        self.addCleanup(self.root.destroy)
        self.addCleanup(self.anim.close)

    def _place_x(self, value: float) -> None:
        self.settings.x = round(value)

    def _gaze_direction(self, pointer: tuple[int, int]) -> int | None:
        return self.visual.gaze_direction(
            pointer,
            game_mode=self.anim.game_mode,
        )

    def _step_walk(self, now: float, elapsed: float) -> str | None:
        return self.animation.advance_walk(
            now, elapsed, game_mode=self.anim.game_mode,
        )

    def test_sprites_and_gaze_do_not_require_hover_ui(self) -> None:
        self.assertFalse(hasattr(self.anim, "pet"))
        self.assertEqual(self.anim.sprites["idle"][0].width(), 192)
        self.anim.show_frame("idle", time.monotonic(), fixed=0)
        self.settings.follow_cursor = False
        self.assertIsNone(self._gaze_direction((10000, 0)))

    def test_movement_uses_injected_geometry_boundary(self) -> None:
        self.walk.movement.remaining_distance = 12
        stride_seconds = self.anim.assets.clips["running-right"].duration_seconds
        travel_seconds = 12 * stride_seconds / 68 + 0.03
        result = self._step_walk(time.monotonic() + 1000, travel_seconds)
        self.assertEqual(result, "running-right")
        assert self.settings.x is not None
        self.assertGreater(self.settings.x, 100)
        self.assertEqual(self.walk.movement.remaining_distance, 0)

    def test_renderer_does_not_own_cursor_observation(self) -> None:
        self.assertFalse(hasattr(self.anim, "observe_pointer"))
        self.assertFalse(hasattr(self.anim, "_cursor_attention"))
        self.assertEqual(self.anim.cursor_eye_position, (196, 582))

    def test_short_frames_advance_without_a_desktop_simulation_tick(self) -> None:
        self.anim.begin_action("waving", time.monotonic())
        self.root.after(195, self.root.quit)
        self.root.mainloop()
        self.assertEqual(self.anim.frame_clock.active_key, ("waving", None))
        self.assertGreaterEqual(self.anim.frame_clock.frame_index, 1)

    def test_waving_replay_displays_original_sprite_by_step(self) -> None:
        now = time.monotonic()
        self.anim.begin_action("waving-greeting", now)
        clip = self.anim.assets.clips["waving-greeting"]
        self.assertEqual(len(clip.frames), 8)
        self.assertEqual(len(clip.timings), 14)
        for index in range(1, 9):
            next_at = (
                self.anim.frame_clock.frame_started_at
                + clip.timings[index - 1] / 1000
                + 0.001
            )
            self.anim.show_frame("waving-greeting", next_at)
        self.assertEqual(self.anim.frame_clock.frame_index, 8)
        self.assertEqual(clip.sprite_index(8), 4)
        rendered = self.canvas.itemcget(self.anim.image_item, "image")
        self.assertEqual(rendered, str(self.anim.sprites["waving"][4]))
        self.assertIs(
            self.anim.sprites["waving"][4],
            self.anim.sprites["waving-greeting"][4],
        )

    def test_sleep_plays_the_full_width_breathing_clip(self) -> None:
        set_test_pet_values(self.state, sleeping=True)
        now = time.monotonic()
        self.anim.render(now, (0, 0))
        self.assertEqual(self.anim.frame_clock.active_key, ("sleep", None))
        first_hold = self.anim.assets.clips["sleep"].timings[0] / 1000
        self.anim.show_frame("sleep", now + first_hold + 0.01)
        self.assertEqual(self.anim.frame_clock.frame_index, 1)
        self.assertEqual(self.anim.sprites["sleep"][0].width(), 192)

    def test_one_shot_returns_to_idle_and_ignores_cancelled_callbacks(self) -> None:
        now = time.monotonic()
        self.anim.begin_action("petting", now)
        old_generation = self.anim._frame_generation
        self.anim.begin_action("eat", now + 0.1)
        initial_deadline = self.action_deadlines[-1]
        self.anim._advance_frame("petting", None, old_generation)
        self.assertEqual(self.anim.frame_clock.active_key, ("eat", None))
        for frame in self.anim.assets.clips["eat"].frames:
            shown_at = self.anim.frame_clock.frame_started_at
            self.anim.show_frame("eat", shown_at + frame.duration_ms / 1000 + 0.01)
        self.assertEqual(self.anim.frame_clock.active_key, ("idle", None))
        self.assertGreater(self.action_deadlines[-1], initial_deadline)
        self.anim.stop()
        self.assertIsNone(self.anim._frame_timer)

    def test_walking_moves_between_desktop_ticks(self) -> None:
        self.settings.follow_cursor = False
        self.walk.movement.remaining_distance = 100
        now = time.monotonic()
        self.anim.render(now, (0, 0))
        self.assertEqual(self.settings.x, 100)
        self.root.after(105, self.root.quit)
        self.root.mainloop()
        assert self.settings.x is not None
        self.assertGreater(self.settings.x, 100)
        self.assertLess(self.settings.x, 108)
        self.assertEqual(self.anim.frame_clock.active_key, ("running-right", None))

    def test_movement_and_visual_settings_have_distinct_owners(self) -> None:
        self.walk.movement.remaining_distance = 30
        self.walk.set_auto_walk(False, now=500)
        self.assertFalse(self.settings.auto_walk)
        self.assertEqual(self.walk.movement.remaining_distance, 0)
        self.assertGreater(self.walk.movement.next_walk_at, 500)
        self.assertIsNotNone(self._gaze_direction((99999, 0)))
        self.settings.follow_cursor = False
        self.visual.reset()
        self.assertFalse(self.settings.follow_cursor)
        self.assertIsNone(self.visual.sector)

    def test_late_frames_still_move_one_stride_per_cycle_at_both_sizes(self) -> None:
        for scale in (1, 2):
            for direction, name in ((1, "running-right"), (-1, "running-left")):
                with self.subTest(scale=scale, direction=direction):
                    self.settings.scale = scale
                    self.settings.x = 100 if direction > 0 else 400
                    start_x = self.settings.x
                    self.anim.reload_sprites()
                    now = time.monotonic()
                    self.walk.movement = WalkController(next_walk_at=now + 100)
                    self.walk.movement.remaining_distance = 1000 * direction
                    self.anim.frame_clock.reset()
                    self.anim.show_frame(name, now)
                    frames = [0]
                    for duration in self.anim.assets.clips[name].timings:
                        now = (
                            self.anim.frame_clock.frame_started_at
                            + duration / 1000
                            + 0.1
                        )
                        # Simulate Tk consuming the scheduled callback first.
                        assert self.anim._frame_timer is not None
                        self.root.after_cancel(self.anim._frame_timer)
                        with patch(
                            "aiko_pet.ui.pet_view.animated_pet.time.monotonic",
                            return_value=now,
                        ):
                            self.anim._advance_frame(
                                name, None, self.anim._frame_generation
                            )
                        frames.append(self.anim.frame_clock.frame_index)
                    self.assertEqual(frames, list(range(8)) + [0])
                    self.assertEqual(self.settings.x, start_x + 68 * scale * direction)

    def test_game_mode_freezes_cursor_gaze_and_uses_existing_pose(self) -> None:
        self.anim.set_game_mode(True)
        self.assertIsNone(self._gaze_direction((99999, -99999)))
        self.assertIsNone(self._step_walk(time.monotonic(), 0.3))
        self.assertIsNone(self.visual.sector)
        self.anim.render(time.monotonic(), (99999, -99999))
        self.assertEqual(self.anim.frame_clock.active_key, ("waiting", None))
        self.anim.begin_action("jumping", time.monotonic())
        self.anim.render(time.monotonic(), (99999, -99999))
        self.assertEqual(self.anim.frame_clock.active_key, ("jumping", None))
        # The shell's canonical playback cancellation precedes its mode change.
        self.anim.cancel_action(time.monotonic())
        self.anim.set_game_mode(False)
        self.assertNotEqual(self.anim.frame_clock.active_key, ("jumping", None))
        self.assertIsNotNone(self._gaze_direction((99999, -99999)))

    def test_idle_blinks_once_then_holds_a_neutral_pose(self) -> None:
        self.settings.auto_walk = False
        self.settings.observe_computer = False
        self.settings.follow_cursor = False
        now = time.monotonic()
        self.anim._ambient.next_blink_at = now - 1
        self.anim._ambient.next_glance_at = now + 200
        self.anim.render(now, (0, 0))
        self.assertTrue(self.anim._ambient.blinking)
        self.assertEqual(self.anim.frame_clock.active_key, ("idle", None))
        observed = [self.anim.frame_clock.frame_index]
        for _ in range(8):
            elapsed = self.anim.assets.clips["idle"].timings[0] / 1000
            step = self.anim.frame_clock.frame_started_at + elapsed + 0.001
            self.anim.show_frame("idle", step)
            if self.anim._ambient.blinking:
                observed.append(self.anim.frame_clock.frame_index)
        self.assertEqual(observed, list(range(8)))
        self.assertFalse(self.anim._ambient.blinking)
        self.assertEqual(self.anim.frame_clock.active_key, ("idle", 0))
        self.assertIsNone(self.anim._frame_timer)
        self.anim.render(now + 2.0, (0, 0))
        self.assertEqual(self.anim.frame_clock.active_key, ("idle", 0))

    def test_aiko_looks_around_even_when_the_pointer_stays_still(self) -> None:
        self.settings.auto_walk = False
        self.settings.observe_computer = False
        now = time.monotonic()
        self.anim._ambient.next_blink_at = now + 200
        self.anim._ambient.next_glance_at = now - 1
        self.anim.render(now, (0, 0))
        active = self.anim.frame_clock.active_key
        assert active is not None
        self.assertEqual(active[0], "look")
        self.assertIn(active[1], (2, 3, 4, 12, 13, 14))
        self.assertIsNone(self.anim._frame_timer)
        self.anim.render(self.anim._ambient._glance_until + 0.1, (0, 0))
        self.assertEqual(self.anim.frame_clock.active_key, ("idle", 0))

    def test_blink_sways_through_every_frame_without_reset_at_both_sizes(self) -> None:
        self.settings.auto_walk = False
        self.settings.observe_computer = False
        self.settings.follow_cursor = False
        for scale in (1, 2):
            with self.subTest(scale=scale):
                self.settings.scale = scale
                self.anim.reload_sprites()
                now = 100.0
                self.anim._ambient.suspend(now - 1.5)
                self.anim._ambient.next_blink_at = now
                self.anim._ambient.next_glance_at = now + 200
                self.anim.frame_clock.reset()
                self.anim.render(now, (0, 0))
                offsets = []
                for frame in range(8):
                    tick = now + frame * .16
                    self.anim.show_frame("idle", tick)
                    self.assertEqual(self.anim.frame_clock.frame_index, frame)
                    offset = self.anim._ambient.motion_offset(tick)
                    offsets.append(offset)
                    expected = self.anim._rest_renderer.resolve(
                        self.anim.sprites["idle"][frame], offset=offset, scale=scale,
                    )
                    self.assertEqual(
                        self.canvas.tk.call(
                            str(self.canvas), "itemcget",
                            self.anim.image_item, "-image",
                        ),
                        str(expected),
                    )
                    self.assertEqual(self.canvas.coords(self.anim.image_item), [0, 0])
                self.assertIn(1, offsets)
                self.assertIn(-1, offsets)
                end = now + 1.28
                self.assertEqual(self.anim._ambient.motion_offset(end), -1)
                self.anim.show_frame("idle", end)
                self.assertFalse(self.anim._ambient.blinking)
                self.assertEqual(self.anim.frame_clock.active_key, ("idle", 0))
                self.assertEqual(self.anim._ambient.motion_offset(end), -1)
                expected = self.anim._rest_renderer.resolve(
                    self.anim.sprites["idle"][0], offset=-1, scale=scale,
                )
                self.assertEqual(
                    self.canvas.tk.call(
                        str(self.canvas), "itemcget", self.anim.image_item, "-image",
                    ), str(expected),
                )

    def test_due_glance_yields_to_object_attention_until_it_is_free(self) -> None:
        self.settings.auto_walk = False
        self.settings.observe_computer = False
        now = time.monotonic()
        ambient = self.anim._ambient
        ambient.next_blink_at = now + 200
        ambient.next_glance_at = now - 1
        ambient._direction = lambda _options: 12
        eyes_x, eyes_y = self.visual._eyes()
        self.visual.object_target = (eyes_x + 1000, eyes_y)
        expected = [("look", 4), ("look", 4), ("body-turn-right", 1)]
        for tick, key in zip((now, now + 1, now + 2), expected):
            self.anim.render(tick, (0, 0))
            self.assertEqual(self.anim.frame_clock.active_key, key)
            self.assertEqual(self.visual.sector, 4)
            self.assertEqual(ambient.next_glance_at, now - 1)
        self.visual.object_target = None
        self.anim.render(now + 3, (0, 0))
        self.assertEqual(self.visual.sector, None)
        self.assertEqual(ambient._glance_frame, 12)
        self.assertEqual(self.anim.frame_clock.active_key, ("body-turn-right", 2))
        self.visual.object_target = (eyes_x + 1000, eyes_y)
        self.anim.render(now + 3.1, (0, 0))
        self.assertEqual(self.visual.sector, 4)
        self.assertEqual(self.anim.frame_clock.active_key, ("body-turn-right", 2))
        self.assertGreater(ambient.next_glance_at, now + 3.1)

    def test_spontaneous_glance_never_overrides_sleep_or_game(self) -> None:
        now = time.monotonic()
        self.anim.set_game_mode(True)
        self.anim._ambient.next_glance_at = now - 1
        self.anim.render(now, (0, 0))
        self.assertEqual(self.anim.frame_clock.active_key, ("waiting", None))
        self.anim.set_game_mode(False)
        set_test_pet_values(self.state, sleeping=True)
        self.anim._ambient.next_glance_at = now - 1
        self.anim.render(now + 1, (0, 0))
        self.assertEqual(self.anim.frame_clock.active_key, ("sleep", None))

    def test_idle_rest_moves_head_without_moving_sprite_anchor(self) -> None:
        self.settings.auto_walk = False
        self.settings.follow_cursor = False
        self.settings.observe_computer = False
        now = time.monotonic()
        self.anim._ambient.suspend(now)
        self.anim._ambient.next_blink_at = now + 200
        self.anim._ambient.next_glance_at = now + 200
        self.anim.render(now, (0, 0))
        image_item = self.anim.image_item
        initial = self.canvas.itemcget(image_item, "image")
        canvas_coords = self.canvas.coords(image_item)
        self.anim.render(now + 0.85, (0, 0))
        changed = self.canvas.itemcget(image_item, "image")
        self.assertNotEqual(initial, changed)
        self.assertEqual(self.canvas.coords(image_item), canvas_coords)
        self.assertEqual(self.anim.frame_clock.active_key, ("idle", 0))
        self.assertIsNone(self.anim._frame_timer)

    def test_still_mouse_gaze_preserves_direction_but_moves_head(self) -> None:
        self.settings.auto_walk = False
        self.settings.observe_computer = False
        now = time.monotonic()
        self.anim._ambient.suspend(now)
        pointer = (99999, 20)
        self.anim.render(
            now,
            pointer,
            attention=CursorAttentionSnapshot(now, -100.0),
        )
        old_key = self.anim.frame_clock.active_key
        assert old_key is not None
        self.assertEqual(old_key[0], "look")
        for elapsed in (1.20, 1.34, 1.48, 1.62):
            self.anim.render(now + elapsed, pointer)
        key = self.anim.frame_clock.active_key
        self.assertEqual(key, ("body-look-right", old_key[1]))
        original = self.canvas.itemcget(self.anim.image_item, "image")
        self.anim.render(now + 2.20, pointer)
        self.assertEqual(self.anim.frame_clock.active_key, key)
        self.assertNotEqual(
            self.canvas.itemcget(self.anim.image_item, "image"),
            original,
        )

    def test_body_turns_do_not_move_desktop_and_scale_keeps_pose(self) -> None:
        self.settings.auto_walk = False
        self.settings.observe_computer = False
        now = time.monotonic()
        self.anim._ambient.next_blink_at = now + 200
        self.anim._ambient.next_glance_at = now + 200
        initial_position = self.settings.x, self.settings.y
        pointer = (99999, 20)
        for elapsed in (0, 1.20, 1.34, 1.48, 1.62):
            self.anim.render(
                now + elapsed,
                pointer,
                attention=CursorAttentionSnapshot(now, -100.0),
            )
        self.assertEqual(self.settings.x, initial_position[0])
        self.assertEqual(self.settings.y, initial_position[1])
        self.assertEqual(self.walk.movement.remaining_distance, 0)
        key = self.anim.frame_clock.active_key
        self.assertEqual(key, ("body-look-right", 4))
        self.settings.scale = 2
        with patch(
            "aiko_pet.ui.pet_view.animated_pet.time.monotonic",
            return_value=now + 1.63,
        ):
            self.anim.reload_sprites()
        self.assertEqual(self.anim.frame_clock.active_key, key)
        self.assertEqual(self.anim.sprites["body-look-right"][4].width(), 384)

    def test_reload_at_double_scale_discards_old_sway_images(self) -> None:
        self.settings.auto_walk = False
        self.settings.follow_cursor = False
        now = time.monotonic()
        self.anim._ambient.suspend(now)
        self.anim._ambient.next_blink_at = now + 100
        self.anim._ambient.next_glance_at = now + 100
        self.anim.render(now + 0.85, (0, 0))
        self.assertTrue(self.anim._rest_renderer._variants)
        self.settings.scale = 2
        self.anim.reload_sprites()
        self.assertEqual(self.anim.sprites["idle"][0].width(), 384)
        self.assertTrue(
            all(
                image.width() == 384
                for image in self.anim._rest_renderer._variants.values()
            )
        )

    def test_scale_reload_keeps_frame_identity(self) -> None:
        self.settings.scale = 2
        self.anim.reload_sprites()
        self.assertEqual(self.anim.sprites["idle"][0].width(), 384)


if __name__ == "__main__":
    unittest.main()
