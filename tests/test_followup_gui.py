"""Real-Tk tests for readable sequential speech and deliberate interruption."""

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.mind.reaction_sequence import Cue
from tools.pet_test_support import set_test_pet_values


class FollowupGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            probe = tk.Tk()
        except tk.TclError as exc:
            raise unittest.SkipTest("Display not available") from exc
        probe.destroy()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = DesktopPet(store=StateStore(Path(self.temp.name) / "pet.json"))
        self.addCleanup(self.app.quit)
        # Controlled speech tests should not be interrupted by the startup
        # greeting that normally runs asynchronously after the first frame.
        if self.app._runtime.scheduled_greeting is not None:
            self.app.root.after_cancel(self.app._runtime.scheduled_greeting)
            self.app._runtime.scheduled_greeting = None
        self.app.settings.auto_routine = False
        set_test_pet_values(self.app.state, sleeping=False)

    def text(self):
        if self.app._speech.bubble is None:
            return None
        return (
            self.app._speech.bubble.winfo_children()[0].winfo_children()[0].cget("text")
        )

    def pass_delay(self, seconds=None):
        time.sleep(seconds or (Cue.text("Oh.").duration_ms / 1000 + 0.08))
        self.app.root.update()

    def test_short_correction_becomes_second_bubble(self):
        self.app._react(
            Reaction(
                "test",
                (
                    Cue.text("Oh."),
                    Cue.text("...Das war unerwartet."),
                ),
                "waiting",
                "click_left",
            )
        )
        self.assertEqual(self.text(), "Oh.")
        self.pass_delay()
        self.assertEqual(self.text(), "...Das war unerwartet.")
        self.assertIsNotNone(self.app._reaction_player.pending_timer)

    def test_new_reaction_cancels_old_followup(self):
        self.app._react(
            Reaction(
                "test",
                (
                    Cue.text("Erster Satz"),
                    Cue.text("Darf nicht mehr auftauchen"),
                ),
                "idle",
                "click_left",
            )
        )
        self.app._react(
            Reaction(
                "other",
                (Cue.text("Eine neue Antwort, die jetzt lesbar bleibt."),),
                "idle",
                "click_right",
            )
        )
        self.pass_delay(1.86)
        self.assertEqual(self.text(), "Eine neue Antwort, die jetzt lesbar bleibt.")

    def test_direct_click_keeps_care_followup_running(self):
        self.app._react(
            Reaction(
                "test",
                (
                    Cue.text("Noch da"),
                    Cue.text("Die laufende Antwort geht weiter."),
                ),
                "idle",
                "care_pet",
            )
        )
        with patch.object(self.app.mind, "click", return_value=None) as click:
            self.app._on_click_left()
        click.assert_not_called()
        self.assertEqual(self.text(), "Noch da")
        self.pass_delay()
        self.assertEqual(self.text(), "Die laufende Antwort geht weiter.")
        self.assertIsNotNone(self.app._reaction_player.pending_timer)

    def test_existing_window_stack_and_hover_are_preserved(self):
        self.app._on_enter()
        self.app._react(
            Reaction(
                "test",
                (
                    Cue.text("Aiko"),
                    Cue.text("...Immer noch Aiko"),
                ),
                "waving",
                "click_left",
            )
        )
        self.app.root.update_idletasks()
        bar = self.app._hover.toolbar
        assert bar is not None
        self.assertTrue(bar.visible)
        self.assertIn(self.app.root, self.app._overlay_windows())
        self.assertIn(self.app._speech.bubble, self.app._overlay_windows())
        self.pass_delay()
        self.assertEqual(self.text(), "...Immer noch Aiko")


if __name__ == "__main__":
    unittest.main()
