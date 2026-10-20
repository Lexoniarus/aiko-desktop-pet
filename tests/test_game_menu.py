"""Selection has no game effects; deferred admission has one owner."""

import tempfile
import tkinter as tk
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from aiko_pet.games.contracts import GameId
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.windows.game_menu import GameMenu
from aiko_pet.ui.windows.tic_tac_toe_window import TicTacToeWindow
from tools.desktop_test_support import create_test_desktop
from tools.tk_test_time import ControlledTkTime


class GameMenuTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timing = self.enterContext(ControlledTkTime())
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pet = create_test_desktop(
            store=StateStore(Path(folder.name) / "save.json"),
        )
        self.addCleanup(self.pet.quit)
        self.hover = self.pet._hover
        self.pet.settings.auto_routine = False
        self.pet.settings.spontaneous_talk = False
        self.pointer = (0, 0)
        self.pointer_widget = None
        self.enterContext(
            patch.object(
                self.pet.root, "winfo_pointerx", side_effect=lambda: self.pointer[0]
            )
        )
        self.enterContext(
            patch.object(
                self.pet.root, "winfo_pointery", side_effect=lambda: self.pointer[1]
            )
        )
        self.enterContext(
            patch.object(
                self.pet.root,
                "winfo_containing",
                side_effect=lambda x, y: (
                    self.pointer_widget if (x, y) == self.pointer else None
                ),
            )
        )
        self.enterContext(
            patch.object(self.pet._input.mouse, "clicked", return_value=False)
        )

    def point_at(self, widget: tk.Widget, x: int, y: int) -> None:
        self.pointer = widget.winfo_rootx() + x, widget.winfo_rooty() + y
        self.pointer_widget = widget
        widget.event_generate("<Motion>", x=x, y=y)
        widget.event_generate("<Enter>", x=x, y=y)

    def open_from_toolbar_click(self) -> GameMenu:
        """Exercise real bindings with simulated input, without cursor warping."""
        self.pet._runtime.stop()
        self.pet._save_hover_position(200, 100)
        self.hover.show_toolbar()
        self.pet.root.update()
        toolbar = self.hover.toolbar
        assert toolbar is not None
        button = toolbar.buttons["play"]
        x, y = button.winfo_width() // 2, button.winfo_height() // 2
        self.point_at(button, x, y)
        button.event_generate("<ButtonPress-1>", x=x, y=y)
        button.event_generate("<ButtonRelease-1>", x=x, y=y)
        menu = self.hover.game_menu
        assert menu is not None
        return menu

    def test_opening_click_survives_delayed_focus_loss_and_allows_selection(self):
        menu = self.open_from_toolbar_click()
        toolbar = self.hover.toolbar
        assert toolbar is not None
        toolbar.buttons["play"].event_generate("<FocusOut>")
        self.assertTrue(self.pet._input._focus_timers)
        self.timing.advance(0.099)
        self.assertIs(self.hover.game_menu, menu)
        self.timing.advance(0.001)
        self.assertFalse(self.pet._input._focus_timers)
        self.assertIs(self.hover.game_menu, menu)
        button = menu.buttons[GameId.TIC_TAC_TOE]
        x, y = button.winfo_width() // 2, button.winfo_height() // 2
        self.point_at(button, x, y)
        button.event_generate("<ButtonPress-1>", x=x, y=y)
        button.event_generate("<ButtonRelease-1>", x=x, y=y)
        self.assertIsNone(self.hover.game_menu)
        self.assertIsInstance(self.hover.game_window, TicTacToeWindow)

    def test_global_poll_of_opening_click_keeps_menu_but_outside_click_closes(self):
        menu = self.open_from_toolbar_click()
        with patch.object(self.pet._input.mouse, "clicked", return_value=True):
            self.pet._input.poll_global_click()
        self.assertIs(self.hover.game_menu, menu)
        self.hover.dismiss_outside(-999, -999)
        self.assertIsNone(self.hover.game_menu)
        self.assertFalse(self.hover.game_open)

    def test_menu_does_not_start_game_or_award_and_outside_dismisses(self) -> None:
        before = self.pet.state.fun
        self.hover.open_game_menu()
        menu = self.hover.game_menu
        assert menu is not None
        self.assertEqual(
            set(menu.buttons),
            set(GameId),
        )
        self.assertFalse(self.hover.game_open)
        self.assertFalse(self.pet._animated.game_mode)
        self.assertIn(menu.frame.winfo_toplevel(), self.pet._overlay_windows())
        self.hover.set_topmost(False)
        self.assertFalse(menu.frame.winfo_toplevel().wm_attributes("-topmost"))
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

    def test_back_releases_menu_and_allows_reopening_without_play(self):
        before = self.pet.state.fun
        self.hover.open_game_menu()
        menu = self.hover.game_menu
        assert menu is not None
        menu.back.invoke()
        self.assertFalse(menu.frame.winfo_exists())
        self.assertIsNone(self.hover.game_menu)
        self.hover.open_game_menu()
        self.assertIsNotNone(self.hover.game_menu)
        self.assertIsNot(self.hover.game_menu, menu)
        self.assertFalse(self.hover.game_open)
        self.assertFalse(self.pet._animated.game_mode)
        self.assertEqual(self.pet.state.fun, before)

    def test_menu_labels_fit_their_buttons_and_escape_has_a_close_binding(self):
        self.hover.open_game_menu()
        menu = self.hover.game_menu
        assert menu is not None
        menu.frame.winfo_toplevel().update()
        self.assertTrue(menu.frame.winfo_toplevel().winfo_ismapped())
        self.assertEqual(
            list(menu.buttons),
            [
                GameId.ROCK_PAPER_SCISSORS,
                GameId.BLACKJACK,
                GameId.TIC_TAC_TOE,
            ],
        )
        for button in menu.buttons.values():
            wrap = self.hover._skin.images.buttons.style.lookup(
                button.cget("style"), "wraplength",
            )
            self.assertLessEqual(int(wrap), button.winfo_width())
        self.assertTrue(menu.frame.winfo_toplevel().bind("<Escape>"))

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
        for game_id in (
            GameId.BLACKJACK,
            GameId.TIC_TAC_TOE,
            GameId.ROCK_PAPER_SCISSORS,
            GameId.BLACKJACK,
        ):
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
