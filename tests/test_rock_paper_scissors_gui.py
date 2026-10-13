"""Real Tk integration: persistent game window, countdown, and cleanup."""

from __future__ import annotations

import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore


class RockPaperScissorsWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            display = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("Tk display unavailable") from error
        display.destroy()

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pet = DesktopPet(store=StateStore(Path(folder.name) / "save.json"))
        self.addCleanup(self.pet.quit)
        self.pet.settings.auto_routine = False
        self.pet.settings.spontaneous_talk = False

    def test_play_opens_one_persistent_window_and_reuses_it(self) -> None:
        self.pet._on_enter()
        toolbar = self.pet._hover.toolbar
        assert toolbar is not None
        original_mood = self.pet.state.mood
        toolbar.buttons["play"].invoke()
        game = self.pet._hover.game_window
        assert game is not None
        self.assertTrue(self.pet._hover.game_open)
        self.assertEqual(game.score.games, 0)
        self.assertEqual(self.pet.state.mood, original_mood)
        self.pet._hover.dismiss_outside(-999, -999)
        self.assertIs(self.pet._hover.game_window, game)
        self.assertTrue(game.window.winfo_exists())
        toolbar.buttons["play"].invoke()
        self.assertIs(self.pet._hover.game_window, game)

    def test_countdown_reveals_only_after_three_beats(self) -> None:
        self.pet._hover.open_game()
        game = self.pet._hover.game_window
        assert game is not None
        game._game._random_index = lambda _size: 2
        game.choose(Move.ROCK)
        self.assertEqual(game.count_label.cget("text"), "1")
        self.assertEqual(game.score.games, 0)
        self.assertEqual(game.buttons[Move.ROCK].cget("state"), "disabled")
        game._advance_countdown()
        self.assertEqual(game.count_label.cget("text"), "2")
        game._advance_countdown()
        self.assertEqual(game.count_label.cget("text"), "3")
        self.assertEqual(game.score.games, 0)
        game._advance_countdown()
        self.assertEqual(game.score.wins, 1)
        self.assertEqual(game.score.games, 1)
        self.assertIn("Aiko: ✌ Schere", game.reveal_label.cget("text"))
        self.assertEqual(game.buttons[Move.ROCK].cget("state"), "normal")

    def test_game_mode_silences_spontaneous_reactions(self) -> None:
        self.pet._hover.open_game()
        self.pet._maybe_show_idle_emote(999999.0)
        self.pet._maybe_speak_spontaneously(999999.0)
        self.assertTrue(self.pet._hover.game_open)
        self.assertIsNone(self.pet._speech.bubble)

    def test_close_aborts_pending_timer_and_restarts_fresh(self) -> None:
        self.pet._hover.open_game()
        game = self.pet._hover.game_window
        assert game is not None
        game.choose(Move.PAPER)
        self.assertIsNotNone(game._timer)
        game.close()
        self.assertFalse(self.pet._hover.game_open)
        self.assertIsNone(self.pet._hover.game_window)
        self.pet._hover.open_game()
        replacement = self.pet._hover.game_window
        assert replacement is not None
        self.assertIsNot(game, replacement)
        self.assertEqual(replacement.score.games, 0)

    def test_status_panel_play_uses_same_window(self) -> None:
        self.pet._hover.open_status()
        panel = self.pet._hover.status_panel
        assert panel is not None
        panel._actions.interact("play")
        self.assertTrue(self.pet._hover.game_open)
        self.assertEqual(self.pet._hover.game_window.score.games, 0)  # type: ignore[union-attr]


if __name__ == "__main__":
    unittest.main()
