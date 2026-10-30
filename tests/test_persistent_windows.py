"""Desktop regressions for one pinnable toolbar and persistent settings."""

from __future__ import annotations

import tempfile
import time
import tkinter as tk
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.commands import NotificationCommand
from aiko_pet.application.events import IncomingNotification
from aiko_pet.games.contracts import GameId
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.windows.action_toolbar import ActionToolbar
from aiko_pet.ui.windows.rock_paper_scissors_window import RockPaperScissorsWindow
from aiko_pet.ui.windows.settings_window import SettingsWindow
from tools.desktop_test_support import create_test_desktop
from tools.pet_test_support import set_test_pet_values


class PersistentWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("No Tk display") from error
        root.destroy()

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pet = create_test_desktop(
            store=StateStore(Path(folder.name) / "state.json"),
        )
        self.addCleanup(self.pet.quit)
        self.pet._runtime.stop()
        self.pet.settings.auto_routine = False
        self.pet.settings.spontaneous_talk = False
        set_test_pet_values(self.pet.state, sleeping=False)
        self.pet.root.update_idletasks()

    def outside(self) -> ExitStack:
        stack = ExitStack()
        for name, value in (
            ("winfo_pointerx", -999),
            ("winfo_pointery", -999),
            ("winfo_containing", None),
        ):
            stack.enter_context(patch.object(self.pet.root, name, return_value=value))
        return stack

    def toolbar(self) -> ActionToolbar:
        self.pet._hover.show_toolbar()
        bar = self.pet._hover.toolbar
        assert bar is not None
        return bar

    def settings(self) -> SettingsWindow:
        self.pet._hover.open_settings(600, 120)
        window = self.pet._hover.settings_window
        assert window is not None
        self.pet.root.update_idletasks()
        return window

    def test_settings_exit_waves_and_speaks_before_shutdown(self) -> None:
        bar = self.toolbar()
        settings = self.settings()
        scheduled: list[tuple[int, object]] = []

        def schedule(delay: int, callback: object) -> str:
            scheduled.append((delay, callback))
            return "test-farewell"

        with patch.object(self.pet._farewell, "_schedule", side_effect=schedule):
            settings.quit_button.invoke()
            self.assertTrue(self.pet._farewell.active)
            self.assertFalse(self.pet._closed)
            self.assertEqual(len(scheduled), 1)
            self.assertGreaterEqual(scheduled[0][0], 2600)
            self.assertEqual(
                self.pet._animated.frame_clock.active_key,
                ("waving-greeting", None),
            )
            self.assertIsNone(self.pet._hover.settings_window)
            self.assertIsNone(self.pet._hover.toolbar)
            self.assertFalse(bar.window.winfo_exists())
            self.assertIsNotNone(self.pet._speech.bubble)
            self.assertTrue(self.pet._input._stopped)
            bubble = self.pet._speech.bubble
            assert bubble is not None
            labels = [
                child
                for frame in bubble.winfo_children()
                for child in frame.winfo_children()
                if isinstance(child, tk.Label)
            ]
            farewell_texts = {
                line.text
                for line in self.pet.mind.book.lines
                if line.event == "farewell"
            }
            self.assertTrue(
                farewell_texts.intersection(str(label.cget("text")) for label in labels)
            )
            self.pet._farewell.begin()
            self.assertEqual(len(scheduled), 1)
            finish = scheduled[0][1]
            assert callable(finish)
            finish()
        self.assertTrue(self.pet._closed)
        self.assertIsNone(self.pet._farewell.pending_timer)
        self.assertTrue(self.pet._lifecycle._stopped)

    def test_direct_quit_cancels_pending_farewell(self) -> None:
        settings = self.settings()
        settings.quit_button.invoke()
        token = self.pet._farewell.pending_timer
        assert token is not None
        self.assertIn(token, self.pet.root.tk.call("after", "info"))
        self.pet.quit()
        self.assertTrue(self.pet._closed)
        self.assertFalse(self.pet._farewell.active)
        self.assertIsNone(self.pet._farewell.pending_timer)

    def test_pin_prevents_both_timeout_and_outside_click(self) -> None:
        bar = self.toolbar()
        bar.pin_button.invoke()
        self.assertTrue(self.pet._hover.keep_open)
        with self.outside():
            self.pet._hover.dismiss_outside(-999, -999)
            self.pet._hover.refresh_hover(time.monotonic() + 100)
            self.assertTrue(bar.visible)
            bar.pin_button.invoke()
            self.assertFalse(self.pet._hover.keep_open)
            self.pet._hover.refresh_hover(time.monotonic() + 100)
            self.assertFalse(bar.visible)

    def test_status_command_reuses_the_same_toolbar(self) -> None:
        bar = self.toolbar()
        windows = len(self.pet.root.winfo_children())
        self.pet._hover.open_status()
        self.pet._hover.open_status()
        self.assertIs(self.pet._hover.toolbar, bar)
        self.assertTrue(self.pet._hover.keep_open)
        self.assertEqual(len(self.pet.root.winfo_children()), windows)
        self.assertFalse(hasattr(self.pet._hover, "status_panel"))

    def test_pin_is_independent_of_topmost_and_saved_position(self) -> None:
        bar = self.toolbar()
        self.pet.set_topmost(False)
        self.pet._save_hover_position(25, 35)
        bar.pin_button.invoke()
        self.assertFalse(self.pet.settings.always_on_top)
        self.assertEqual(
            (self.pet.settings.toolbar_x, self.pet.settings.toolbar_y), (25, 35)
        )
        self.pet.reset_toolbar_position()
        self.assertTrue(self.pet._hover.keep_open)
        self.assertIsNone(self.pet.settings.toolbar_x)
        self.assertNotIn("keep_open", self.pet.settings.to_dict())

    def test_settings_survive_outside_click_and_toolbar_timeout(self) -> None:
        bar = self.toolbar()
        window = self.settings()
        with self.outside():
            self.pet._hover.dismiss_outside(-999, -999)
            self.pet._hover.refresh_hover(time.monotonic() + 100)
        self.assertFalse(bar.visible)
        self.assertIs(self.pet._hover.settings_window, window)
        self.assertTrue(window.window.winfo_exists())

    def test_settings_reopen_focuses_existing_instance(self) -> None:
        window = self.settings()
        with patch.object(window, "focus") as focus:
            self.pet._hover.open_settings(20, 30)
        focus.assert_called_once()
        self.assertIs(self.pet._hover.settings_window, window)

    def test_settings_position_survives_updates_and_close_reopen(self) -> None:
        window = self.settings()
        window.window.geometry("+80+60")
        self.pet.root.update_idletasks()
        self.pet.center()
        window.scale_buttons[2].invoke()
        self.pet._hover.refresh_settings()
        self.pet.root.update_idletasks()
        self.assertEqual(
            (window.window.winfo_rootx(), window.window.winfo_rooty()), (80, 60)
        )
        window.close()
        replacement = self.settings()
        self.assertEqual(replacement.position, (80, 60))
        self.assertIsNot(replacement, window)

    def test_opening_and_pinning_windows_do_not_register_contact(self) -> None:
        before = self.pet.state.capture_checkpoint()
        contact_at = self.pet.mind.last_contact
        with patch.object(self.pet._world, "interrupt") as interrupt:
            self.pet._hover.open_status()
            self.settings()
            bar = self.toolbar()
            bar.pin_button.invoke()
        interrupt.assert_not_called()
        self.assertEqual(self.pet.mind.last_contact, contact_at)
        self.assertEqual(self.pet.state.capture_checkpoint(), before)

    def test_notification_is_delivered_with_idle_pinned_windows(self) -> None:
        self.pet._hover.open_status()
        self.settings()
        self.pet._action_playback.until = 0
        self.pet._attention.last_spoken = -1000
        self.pet.application.dispatch(
            NotificationCommand(
                IncomingNotification(
                    event_id="persistent-windows",
                    source="test.browser",
                    title="Kalender",
                    message="Termin gleich.",
                )
            )
        )
        with self.outside(), patch.object(self.pet._speech, "show_text") as show:
            self.pet._present_pending_notification(time.monotonic())
        show.assert_called_once_with("Kalender: Termin gleich.", 3500)
        self.assertIsNone(self.pet.application.next_notification())

    def test_shared_skin_is_reused_by_all_three_windows(self) -> None:
        bar = self.toolbar()
        settings = self.settings()
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        game = self.pet._hover.game_window
        assert isinstance(game, RockPaperScissorsWindow)
        self.assertIs(bar.skin, settings.skin)
        self.assertIs(bar.skin, game.skin)

    def test_settings_close_notifies_owner_and_releases_drag(self) -> None:
        window = self.settings()
        event = tk.Event()
        event.x_root, event.y_root = 80, 90
        window._drag.start(event)
        window.close()
        window.close()
        self.assertIsNone(self.pet._hover.settings_window)
        self.assertFalse(window.dragging)


if __name__ == "__main__":
    unittest.main()
