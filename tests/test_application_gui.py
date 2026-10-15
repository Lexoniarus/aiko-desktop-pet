"""Tk-boundary tests for care command dispatch and queued notifications."""

from __future__ import annotations

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.commands import CareCommand, NotificationCommand
from aiko_pet.application.events import IncomingNotification
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore


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
        self.pet = DesktopPet(store=StateStore(Path(folder.name) / "state.json"))
        self.addCleanup(self.pet.quit)
        self.pet.settings.auto_routine = False
        self.pet.settings.spontaneous_talk = False
        self.pet.state.sleeping = False
        if self.pet._runtime.scheduled_greeting is not None:
            self.pet.root.after_cancel(self.pet._runtime.scheduled_greeting)
            self.pet._runtime.scheduled_greeting = None

    def _notice(self, identifier: str) -> IncomingNotification:
        return IncomingNotification(
            event_id=identifier, source="test.browser",
            title="Kalender", message="Termin gleich.",
        )

    def _bubble_text(self) -> str | None:
        bubble = self.pet._speech.bubble
        if bubble is None:
            return None
        children = bubble.winfo_children()
        frame = children[0]
        children = frame.winfo_children()
        return str(children[0].cget("text"))

    def test_care_passes_through_application_controller(self) -> None:
        self.pet.state.affection = 10
        with patch.object(
            self.pet.application, "dispatch",
            wraps=self.pet.application.dispatch,
        ) as dispatch:
            self.pet.interact("pet")
        self.assertAlmostEqual(self.pet.state.affection, 35, places=3)
        self.assertIsInstance(dispatch.call_args.args[0], CareCommand)
        self.assertEqual(dispatch.call_args.args[0].action, "pet")
        self.assertIsNotNone(self.pet._speech.bubble)

    def test_care_uses_new_one_shot_clips_and_sleep_cancels_them(self) -> None:
        self.pet.interact("feed")
        self.assertEqual(self.pet._action_playback.state, "eat")
        self.assertEqual(self.pet._animated.frame_clock.active_key, ("eat", None))
        self.pet.interact("pet")
        self.assertEqual(self.pet._action_playback.state, "petting")
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
        self.assertNotEqual(self.pet._action_playback.state, "attack")

    def test_late_care_frames_extend_the_host_action_deadline(self) -> None:
        now = time.monotonic()
        self.pet._start_action("eat", 0, started_at=now)
        original_deadline = self.pet._action_playback.until
        late = now + 3
        self.pet._animated.render(late, .14, (0, 0))
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
        self.pet.state.sleeping = True
        self.pet._tick()
        self.assertIsNone(self._bubble_text())
        self.pet.state.sleeping = False
        self.pet._attention.last_spoken = time.monotonic() - 10
        self.pet._tick()
        self.assertEqual(self._bubble_text(), "Kalender: Termin gleich.")


if __name__ == "__main__":
    unittest.main()
