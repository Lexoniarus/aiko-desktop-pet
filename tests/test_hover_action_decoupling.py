"""Passive controls must not acquire character action ownership."""

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.commands import NotificationCommand
from aiko_pet.application.events import IncomingNotification
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

    def test_world_motion_continues_under_sprite_toolbar_and_bridge(self):
        for scale in (1, 2):
            if self.pet.settings.scale != scale:
                self.pet.toggle_scale()
            for region in ("sprite", "toolbar", "bridge", "outside"):
                with self.subTest(scale=scale, region=region):
                    self.pet._hover.show_toolbar()
                    self.pet.root.update_idletasks()
                    bar = self.pet._hover.toolbar
                    assert bar is not None
                    x = self.pet.settings.x or 0
                    self.pet._walk.set_world_goal(x + 30)
                    request = self.pet._walk.movement.request("world")
                    with (
                        patch.object(self.pet.root, "winfo_pointerx",
                                     return_value=x + 96 * scale),
                        patch.object(self.pet.root, "winfo_pointery", return_value=100),
                        patch.object(self.pet.root, "winfo_containing",
                                     return_value=self.pet.canvas if region == "sprite"
                                     else None),
                        patch.object(bar, "contains_pointer",
                                     return_value=region == "toolbar"),
                        patch.object(bar, "contains_bridge",
                                     return_value=region == "bridge"),
                    ):
                        step = self.pet._walk.step(
                            time.monotonic(), .1,
                            game_mode=False, attention_active=False,
                        )
                    self.assertIsNotNone(step)
                    self.assertGreater(self.pet.settings.x or 0, x)
                    self.assertIs(self.pet._walk.movement.request("world"), request)

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

    def test_visible_controls_do_not_defer_a_free_notification_slot(self):
        for view in ("toolbar", "settings"):
            with self.subTest(view=view):
                self.pet._speech.hide()
                self.pet._attention.last_spoken = -1000
                self.pet._hover.show_toolbar()
                if view == "settings":
                    self.pet._hover.open_settings(100, 100)
                    window = self.pet._hover.settings_window
                else:
                    window = self.pet._hover.toolbar
                assert window is not None
                self.pet.root.update_idletasks()
                self.pet.application.dispatch(NotificationCommand(IncomingNotification(
                    event_id=view, source="test.hover", title="Termin", message=view,
                )))
                with (
                    patch.object(self.pet.root, "winfo_pointerx",
                                 return_value=window.window.winfo_rootx() + 20),
                    patch.object(self.pet.root, "winfo_pointery",
                                 return_value=window.window.winfo_rooty() + 20),
                ):
                    self.pet._attention_runtime.present_notification(time.monotonic())
                self.assertIsNotNone(self.pet._speech.bubble)
