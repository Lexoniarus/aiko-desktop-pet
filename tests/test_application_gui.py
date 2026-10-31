"""Tk-boundary tests for care command dispatch and queued notifications."""

from __future__ import annotations

import math
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.commands import CareCommand, NotificationCommand
from aiko_pet.application.events import IncomingNotification
from aiko_pet.infrastructure.persistence import StateStore
from tools.desktop_test_support import create_test_desktop
from tools.pet_test_support import set_test_pet_values


class ApplicationGuiBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            probe = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("No usable graphical display") from error
        probe.destroy()

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pet = create_test_desktop(
            store=StateStore(Path(folder.name) / "state.json"),
        )
        self.addCleanup(self.pet.quit)
        # These command tests own pointer input; a real cursor over the sprite
        # legitimately opens controls and defers notifications on a live desktop.
        for method in ("winfo_pointerx", "winfo_pointery"):
            self.enterContext(patch.object(self.pet.root, method, return_value=0))
        self.enterContext(patch.object(self.pet.root, "winfo_containing",
                                       return_value=None))
        self.pet._hover.close_toolbar()
        self.pet.settings.auto_routine = False
        self.pet.settings.spontaneous_talk = False
        set_test_pet_values(self.pet.state, sleeping=False)
        if self.pet._runtime.scheduled_greeting is not None:
            self.pet.root.after_cancel(self.pet._runtime.scheduled_greeting)
            self.pet._runtime.scheduled_greeting = None

    def _notice(self, identifier: str) -> IncomingNotification:
        return IncomingNotification(
            event_id=identifier, source="test.browser",
            title="Kalender", message="Termin gleich.",
        )

    def _watch_moving_cursor(self):
        """Build real attention through the assembled sensor/policy path."""
        self.pet._runtime.stop()
        self.pet._action_playback.cancel_at(time.monotonic())
        self.pet._reaction_player.cancel()
        self.pet.settings.auto_walk = self.pet.settings.follow_cursor = True
        self.pet.root.update_idletasks()
        eyes = self.pet._animated.cursor_eye_position
        width = 192 * self.pet.settings.scale
        native = [0, 0]
        self.enterContext(patch.object(self.pet.root, "winfo_pointerx",
                                      side_effect=lambda: native[0]))
        self.enterContext(patch.object(self.pet.root, "winfo_pointery",
                                      side_effect=lambda: native[1]))
        now = time.monotonic()
        for n in range(45):
            sample_time = now - 6.3 + n * .14
            native[:] = (
                round(eyes[0] + width * (2.4 + .7 * math.cos(n * .63))),
                round(eyes[1] - width * (.8 + .7 * math.sin(n * .63))),
            )
            self.pet._pointer_runtime.observe(sample_time)
            self.pet._pointer_runtime.begin_behaviour(sample_time)
        self.pet._speech.hide()
        self.assertTrue(self.pet._cursor_behaviour.watching)
        self.assertEqual(self.pet._cursor_behaviour.intent.attention, 100)
        return native

    def test_native_and_polled_flyover_open_toolbar_and_preserve_tracking(self):
        for scale in (1, 2):
            with self.subTest(scale=scale):
                self.pet._hover.close_toolbar()
                self.pet.settings.scale = scale
                self.pet._window.resize()
                self.pet._animated.reload_sprites()
                self.pet._pointer_runtime.reset()
                native = self._watch_moving_cursor()
                before = self.pet.state.capture_checkpoint()
                native[:] = (self.pet.root.winfo_x() + 96 * scale,
                             self.pet.root.winfo_y() + 120 * scale)
                with patch.object(self.pet._world, "interrupt") as interrupt:
                    self.pet._input.on_enter()
                    now = time.monotonic()
                    self.pet._hover.refresh_hover(now)
                    self.pet._pointer_runtime.observe(now)
                    self.pet._pointer_runtime.begin_behaviour(now)
                interrupt.assert_not_called()
                toolbar = self.pet._hover.toolbar
                assert toolbar is not None
                self.assertTrue(toolbar.visible)
                self.assertTrue(self.pet._cursor_behaviour.watching)
                self.assertEqual(self.pet._cursor_behaviour.intent.attention, 100)
                self.assertFalse(self.pet._cursor_behaviour._policy._access)
                self.assertEqual(self.pet.state.capture_checkpoint(), before)

    def test_tracking_toolbar_does_not_hold_world_motion(self):
        native = self._watch_moving_cursor()
        self.pet._hover.show_toolbar()
        toolbar = self.pet._hover.toolbar
        assert toolbar is not None
        self.pet.root.update_idletasks()
        native[:] = (toolbar.window.winfo_rootx() + 20,
                     toolbar.window.winfo_rooty() + 20)
        now = time.monotonic()
        self.pet._pointer_runtime.observe(now)
        self.pet._pointer_runtime.begin_behaviour(now)
        self.assertTrue(self.pet._cursor_behaviour.watching)
        self.assertGreater(self.pet._cursor_behaviour.intent.attention, 0)
        self.assertFalse(self.pet._cursor_behaviour._policy._access)
        x = self.pet.settings.x or 0
        track = self.pet._window.track
        goal = x + 40 if x + self.pet._window.width + 40 < track.right else x - 40
        self.pet._walk.set_world_goal(goal)
        self.assertIsNotNone(self.pet._walk.step(
            now, .1, game_mode=False, attention_active=False,
        ))
        self.assertGreater(abs((self.pet.settings.x or 0) - x), 0)
        self.assertEqual(self.pet._walk.movement.goal_x, goal)
        native[:] = (0, 0)
        self.assertTrue(toolbar.visible)
        self.assertIsNotNone(self.pet._walk.step(
            now + .1, .1, game_mode=False, attention_active=False,
        ))

    def _bubble_text(self) -> str | None:
        bubble = self.pet._speech.bubble
        if bubble is None:
            return None
        children = bubble.winfo_children()
        frame = children[0]
        children = frame.winfo_children()
        return str(children[0].cget("text"))

    def test_care_passes_through_application_controller(self) -> None:
        set_test_pet_values(self.pet.state, affection=10)
        with patch.object(
            self.pet.application._care._clock, "consume", return_value=0.0,
        ), patch.object(
            self.pet.application, "dispatch", wraps=self.pet.application.dispatch,
        ) as dispatch:
            self.pet.interact("pet")
        self.assertAlmostEqual(self.pet.state.affection, 35, places=3)
        self.assertIsInstance(dispatch.call_args.args[0], CareCommand)
        self.assertEqual(dispatch.call_args.args[0].action, "pet")
        self.assertIsNotNone(self.pet._speech.bubble)

    def test_care_uses_new_one_shot_clips_and_sleep_cancels_them(self) -> None:
        set_test_pet_values(self.pet.state, affection=10)
        self.pet.interact("feed")
        self.assertEqual(self.pet._action_playback.clip_id, "eat")
        self.assertEqual(self.pet._animated.frame_clock.active_key, ("eat", None))
        self.pet.interact("pet")
        self.assertEqual(self.pet._action_playback.clip_id, "petting")
        self.assertEqual(self.pet._animated.frame_clock.active_key,
                         ("petting", None))
        self.pet.interact("sleep")
        self.assertTrue(self.pet.state.sleeping)
        self.assertEqual(self.pet._animated.frame_clock.active_key, ("sleep", None))
        self.assertLessEqual(self.pet._action_playback.until, time.monotonic())
        self.pet.interact("sleep")
        self.assertFalse(self.pet.state.sleeping)
        self.assertNotEqual(self.pet._animated.frame_clock.active_key,
                            ("petting", None))
        self.assertNotEqual(self.pet._action_playback.clip_id, "attack")

    def test_late_care_frames_extend_the_host_action_deadline(self) -> None:
        now = time.monotonic()
        self.pet._start_action("eat", 0, started_at=now)
        original_deadline = self.pet._action_playback.until
        late = now + 3
        self.pet._animated.render(late, (0, 0))
        self.assertEqual(self.pet._animated.frame_clock.active_key, ("eat", None))
        self.assertEqual(self.pet._animated.frame_clock.frame_index, 1)
        self.assertGreater(self.pet._action_playback.until, original_deadline)
        self.assertGreater(self.pet._action_playback.until, late)
        for frame in self.pet._character_assets.clips["eat"].frames[1:]:
            shown_at = self.pet._animated.frame_clock.frame_started_at
            self.pet._animated.show_frame(
                "eat", shown_at + frame.duration_ms / 1000 + .01,
            )
        self.assertEqual(self.pet._animated.frame_clock.active_key, ("idle", None))

    def test_save_advances_in_application_before_disk_write(self) -> None:
        steps: list[str] = []
        with (
            patch.object(
                self.pet._activity, "advance_state",
                side_effect=lambda _stamp: steps.append("advance"),
            ),
            patch.object(
                self.pet._persistence, "save",
                side_effect=lambda: steps.append("write"),
            ),
        ):
            self.pet._save()
        self.assertEqual(steps, ["advance", "write"])

    def test_browser_notification_only_displays_when_undisturbed(self) -> None:
        self.pet._speech.show_text("Schon am Reden", 4000)
        response = self.pet.application.dispatch(
            NotificationCommand(self._notice("browser-1")),
        )
        self.assertEqual(response.status, "accepted")
        self.pet._tick()
        self.assertEqual(self._bubble_text(), "Schon am Reden")
        self.pet._speech.hide()
        self.pet._attention.last_spoken = time.monotonic() - 10
        self.pet._tick()
        self.assertEqual(self._bubble_text(), "Kalender: Termin gleich.")
        self.assertIsNone(self.pet.application.next_notification())

    def test_sleeping_defers_notification_until_awake(self) -> None:
        self.pet.application.dispatch(
            NotificationCommand(self._notice("browser-2")),
        )
        set_test_pet_values(self.pet.state, sleeping=True)
        self.pet._tick()
        self.assertIsNone(self._bubble_text())
        set_test_pet_values(self.pet.state, sleeping=False)
        self.pet._attention.last_spoken = time.monotonic() - 10
        self.pet._tick()
        self.assertEqual(self._bubble_text(), "Kalender: Termin gleich.")

    def test_hovered_controls_allow_notification_immediately(self) -> None:
        self.pet.application.dispatch(NotificationCommand(self._notice("hover")))
        with patch.object(self.pet.root, "winfo_containing",
                          return_value=self.pet.canvas):
            self.pet._tick()
            self.assertEqual(self._bubble_text(), "Kalender: Termin gleich.")
        self.pet._hover.last_hover = time.monotonic() - 10
        self.pet._attention.last_spoken = time.monotonic() - 10
        self.pet._tick()
        self.assertEqual(self._bubble_text(), "Kalender: Termin gleich.")


if __name__ == "__main__":
    unittest.main()
