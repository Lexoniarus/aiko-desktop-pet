"""Small real-Tk tests for intentionally awkward, two-part speech bubbles."""

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import tkinter as tk

from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore


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
        self.app.state.sleeping = False

    def text(self):
        if self.app._speech.bubble is None:
            return None
        return self.app._speech.bubble.winfo_children()[0].winfo_children()[0].cget("text")

    def pass_delay(self):
        time.sleep(0.68)
        self.app.root.update()

    def test_short_correction_becomes_second_bubble(self):
        self.app._react(Reaction("test", "Oh.", "waiting", "click_left",
                                 "...Das war unerwartet.", 600))
        self.assertEqual(self.text(), "Oh.")
        self.pass_delay()
        self.assertEqual(self.text(), "...Das war unerwartet.")
        self.assertIsNone(self.app._reaction_player.pending_timer)

    def test_new_reaction_cancels_old_followup(self):
        self.app._react(Reaction("test", "Erster Satz", "idle", "click_left",
                                 "Darf nicht mehr auftauchen", 600))
        self.app._react(Reaction("other", "Neuer Satz", "idle", "click_right"))
        self.pass_delay()
        self.assertEqual(self.text(), "Neuer Satz")

    def test_deliberate_click_silence_cancels_pending_followup(self):
        self.app._react(Reaction("test", "Noch da", "idle", "click_left",
                                 "Das darf nicht kommen", 600))
        with patch.object(self.app.mind, "click", return_value=None):
            self.app._on_click_left()
        self.assertIsNone(self.app._speech.bubble)
        self.pass_delay()
        self.assertIsNone(self.app._speech.bubble)
        self.assertIsNone(self.app._reaction_player.pending_timer)

    def test_existing_window_stack_and_hover_are_preserved(self):
        self.app._on_enter()
        self.app._react(Reaction("test", "Aiko", "waving", "click_left",
                                 "...Immer noch Aiko", 600))
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
