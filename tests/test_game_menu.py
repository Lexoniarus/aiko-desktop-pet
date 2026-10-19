"""Selection has no game effects; deferred admission has one owner."""

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from tkinter import font as tkfont
from unittest.mock import patch

from aiko_pet.games.contracts import GameId
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore


class GameMenuTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pet = DesktopPet(store=StateStore(Path(folder.name) / "save.json"))
        self.addCleanup(self.pet.quit)
        self.hover = self.pet._hover
        self.pet.settings.auto_routine = False
        self.pet.settings.spontaneous_talk = False

    def test_menu_does_not_start_game_or_award_and_outside_dismisses(self) -> None:
        before = self.pet.state.fun
        self.hover.open_game_menu()
        menu = self.hover.game_menu
        assert menu is not None
        self.assertEqual(
            set(menu.buttons), set(GameId),
        )
        self.assertFalse(self.hover.game_open)
        self.assertFalse(self.pet._animated.game_mode)
        self.assertIn(menu.window, self.pet._overlay_windows())
        self.hover.set_topmost(False)
        self.assertFalse(menu.window.wm_attributes("-topmost"))
        self.hover.dismiss_outside(-999, -999)
        self.assertIsNone(self.hover.game_menu)
        self.assertEqual(self.pet.state.fun, before)

    def test_selection_closes_menu_and_opens_one_game(self) -> None:
        self.hover.open_game_menu()
        menu = self.hover.game_menu
        assert menu is not None
        menu.choose(GameId.ROCK_PAPER_SCISSORS)
        game = self.hover.game_window
        self.assertIsNotNone(game)
        self.assertIsNone(self.hover.game_menu)
        menu.choose(GameId.ROCK_PAPER_SCISSORS)
        self.hover.open_game_menu()
        self.assertIs(self.hover.game_window, game)
        self.assertIsNone(self.hover.game_menu)

    def test_menu_labels_fit_their_buttons_and_escape_has_a_close_binding(self):
        self.hover.open_game_menu()
        menu = self.hover.game_menu
        assert menu is not None
        menu.window.update_idletasks()
        self.assertEqual(list(menu.buttons), [
            GameId.ROCK_PAPER_SCISSORS, GameId.BLACKJACK, GameId.TIC_TAC_TOE,
        ])
        for button in menu.buttons.values():
            font = tkfont.Font(root=self.pet.root, font=button.cget("font"))
            self.assertLess(font.measure(button.cget("text")), button.winfo_width())
        self.assertTrue(menu.window.bind("<Escape>"))

    def test_deferred_selection_is_reserved_and_stale_callback_cannot_start(self):
        callbacks = []
        with patch.object(self.pet._world, "interrupt", side_effect=callbacks.append):
            self.hover.open_game(GameId.ROCK_PAPER_SCISSORS)
            self.hover.open_game(GameId.ROCK_PAPER_SCISSORS)
            self.assertTrue(self.hover.game_open)
            self.assertEqual(len(callbacks), 1)
            self.hover.close_game()
            callbacks[0]()
        self.assertFalse(self.hover.game_open)
        self.assertIsNone(self.hover.game_window)

    def test_constructor_failure_releases_mode_and_reservation(self) -> None:
        with patch(
            "aiko_pet.ui.windows.hover_ui.RockPaperScissorsWindow",
            side_effect=RuntimeError("construction failed"),
        ):
            with self.assertRaises(RuntimeError):
                self.hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        self.assertFalse(self.hover.game_open)
        self.assertFalse(self.pet._animated.game_mode)

    def test_each_menu_choice_closes_cleanly_and_starts_a_fresh_session(self):
        before = self.pet.state.fun
        for game_id in (GameId.BLACKJACK, GameId.TIC_TAC_TOE,
                        GameId.ROCK_PAPER_SCISSORS, GameId.BLACKJACK):
            self.hover.open_game_menu()
            menu = self.hover.game_menu
            assert menu is not None
            menu.choose(game_id)
            self.assertTrue(self.hover.game_open)
            self.assertTrue(self.pet._animated.game_mode)
            self.hover.close_game()
            self.assertFalse(self.hover.game_open)
            self.assertFalse(self.pet._animated.game_mode)
            self.assertEqual(self.pet._game_visuals.hand.windows, ())
            self.assertIsNone(self.pet._speech.bubble)
        self.assertEqual(self.pet.state.fun, before)

    def test_recheck_admission_and_shutdown_clear_pending_selection(self) -> None:
        callbacks = []
        with patch.object(self.pet._world, "interrupt", side_effect=callbacks.append):
            self.hover.open_game(GameId.ROCK_PAPER_SCISSORS)
            original = self.hover._ports
            self.hover._ports = replace(original, game_ready=lambda: False)
            callbacks[0]()
            self.hover._ports = original
            self.assertFalse(self.hover.game_open)
            self.hover.open_game(GameId.ROCK_PAPER_SCISSORS)
            self.pet.quit()
            callbacks[1]()
        self.assertIsNone(self.hover.game_window)
