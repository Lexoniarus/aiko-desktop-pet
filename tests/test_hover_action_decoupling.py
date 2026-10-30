"""Passive controls must not acquire character action ownership."""

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.infrastructure.persistence import StateStore
from tools.desktop_test_support import create_test_desktop
from tools.pet_test_support import set_test_pet_values


class HoverActionDecouplingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            probe = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest(str(error)) from error
        probe.destroy()

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pet = create_test_desktop(
            store=StateStore(Path(folder.name) / "state.json"),
        )
        self.addCleanup(self.pet.quit)
        self.pet._runtime.stop()
        self.pet.settings.auto_routine = False
        self.pet.settings.auto_walk = True
        self.pet.settings.follow_cursor = False
        self.pet.settings.observe_computer = False
        set_test_pet_values(self.pet.state, sleeping=False, energy=90)
        self.pet._action_playback.cancel_at(time.monotonic())
        self.pet._reaction_player.cancel()
        self.pet._place_x(200)
        self.pet.root.update_idletasks()

    def test_opening_pinning_and_browsing_preserve_contact_and_departure_clock(self):
        before = self.pet.state.capture_checkpoint()
        contact_at = self.pet.mind.last_contact
        next_step = self.pet._walk.movement.next_walk_at
        with patch.object(self.pet._world, "interrupt") as interrupt:
            for _ in range(3):
                self.pet._input.on_enter()
            self.pet._hover.open_status()
            bar = self.pet._hover.toolbar
            assert bar is not None
            bar.pin_button.invoke()
            bar.toggle_details()
            self.pet._hover.open_social_menu()
            self.pet._hover.open_game_menu()
            self.pet._hover.open_food_menu()
            self.pet._hover.open_settings(100, 100)
            self.pet.root.update_idletasks()
        interrupt.assert_not_called()
        self.assertEqual(self.pet.mind.last_contact, contact_at)
        self.assertEqual(self.pet.state.capture_checkpoint(), before)
        self.assertEqual(self.pet._walk.movement.next_walk_at, next_step)

    def test_explicit_accepted_contact_still_claims_cursor_and_interrupts_motion(self):
        self.pet._walk.set_world_goal(500)
        with patch.object(self.pet._pointer_runtime, "claim_access",
                          wraps=self.pet._pointer_runtime.claim_access) as claim:
            self.pet._input.on_left_click()
        claim.assert_called_once_with()
        self.assertIsNone(self.pet._walk.movement.goal_x)
        self.assertEqual(len(self.pet.mind.clicks), 1)
