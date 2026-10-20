"""Board input, round controls and care completion through the actual host."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.games.contracts import GameId
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.windows.tic_tac_toe_window import TicTacToeWindow
from tools.desktop_test_support import create_test_desktop
from tools.tk_test_time import ControlledTkTime


class TicTacToeGuiTests(unittest.TestCase):
    def setUp(self):
        self.timing = self.enterContext(ControlledTkTime())
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pet = create_test_desktop(
            store=StateStore(Path(folder.name) / "save.json"),
        )
        self.addCleanup(self.pet.quit)
        self.pet._hover.open_game(GameId.TIC_TAC_TOE)
        game = self.pet._hover.game_window
        assert isinstance(game, TicTacToeWindow)
        self.game: TicTacToeWindow = game
        self.game._sequence.game._random_index = lambda _size: 0

    def test_buttons_result_next_round_and_once_only_reward(self):
        game = self.game
        before = self.pet.state.fun
        for cell in (0, 8, 6):
            game.buttons[cell].invoke()
            self.assertTrue(all(b.cget("state") == "disabled" for b in game.buttons))
            game._sequence.advance()
        game.buttons[7].invoke()
        next_button = game._panel.next_button
        assert next_button is not None
        self.assertEqual(next_button.cget("state"), "normal")
        self.assertEqual(game.buttons[7].cget("bg"), game.skin.accent)
        self.assertEqual(self.pet.state.fun, before)
        next_button.invoke()
        self.assertEqual(game._sequence.game.board.turn, "O")
        game.close()
        after = self.pet.state.fun
        self.assertGreater(after, before)
        game.close()
        self.assertEqual(self.pet.state.fun, after)
        self.assertIsNone(self.pet._hover.game_window)

    def test_pending_turn_does_not_reward_and_callbacks_are_cancelled(self):
        before = self.pet.state.fun
        self.game.buttons[0].invoke()
        self.game.close()
        self.game._sequence.advance()
        self.assertEqual(self.pet.state.fun, before)
        self.assertIsNone(self.game._sequence.pending_timer)

    def test_system_close_cancels_pending_turn_and_releases_the_host(self):
        before = self.pet.state.fun
        self.game.buttons[0].invoke()
        pending = self.game._sequence.pending_timer
        assert pending is not None
        self.pet.root.tk.eval(self.game.window.protocol("WM_DELETE_WINDOW"))
        self.game._sequence.advance()
        self.game.close()
        self.assertNotIn(pending, self.pet.root.tk.call("after", "info"))
        self.assertIsNone(self.game._sequence.pending_timer)
        self.assertFalse(self.game.window.winfo_exists())
        self.assertIsNone(self.pet._hover.game_window)
        self.assertFalse(self.pet._animated.game_mode)
        self.assertIsNone(self.pet._speech.bubble)
        self.assertEqual(self.pet.state.fun, before)
        self.pet._hover.open_game(GameId.TIC_TAC_TOE)
        self.assertIsNotNone(self.pet._hover.game_window)

    def test_failed_construction_releases_partial_panel_and_allows_retry(self):
        for target in (
            "aiko_pet.ui.windows.tic_tac_toe_window.TicTacToeWindow._present",
            "aiko_pet.ui.windows.tic_tac_toe_window.GamePanel.show",
        ):
            with self.subTest(failure=target):
                self.pet._hover.close_game()
                before_widgets = set(self.pet.root.winfo_children())
                before_fun = self.pet.state.fun
                with (
                    patch(target, side_effect=RuntimeError("panel setup failed")),
                    patch.object(self.pet.application, "complete_game") as completed,
                ):
                    with self.assertRaisesRegex(RuntimeError, "panel setup failed"):
                        self.pet._hover.open_game(GameId.TIC_TAC_TOE)
                completed.assert_not_called()
                self.assertEqual(set(self.pet.root.winfo_children()), before_widgets)
                self.assertFalse(self.pet._hover.game_open)
                self.assertIsNone(self.pet._hover.game_window)
                self.assertFalse(self.pet._animated.game_mode)
                self.assertIsNone(self.pet._speech.bubble)
                self.assertEqual(self.pet.state.fun, before_fun)
                self.pet._hover.open_game(GameId.TIC_TAC_TOE)
                game = self.pet._hover.game_window
                assert isinstance(game, TicTacToeWindow)
                self.assertEqual(len(game.buttons), 9)
                self.assertEqual(game._sequence.game.score.games, 0)
