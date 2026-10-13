"""Tk integration: game input only; Aiko narrates from her own bubble."""

from __future__ import annotations

import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore


def bubble_text(pet: DesktopPet) -> str | None:
    bubble = pet._speech.bubble
    if bubble is None:
        return None
    frame = bubble.winfo_children()[0]
    return str(frame.winfo_children()[0].cget("text"))


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

    def test_game_is_kenney_styled_input_only_and_stays_open(self) -> None:
        self.pet._on_enter()
        toolbar = self.pet._hover.toolbar
        assert toolbar is not None
        before = self.pet.state.mood
        toolbar.buttons["play"].invoke()
        game = self.pet._hover.game_window
        assert game is not None
        self.assertTrue(self.pet._hover.game_open)
        self.assertEqual(game.score.games, 0)
        self.assertEqual(self.pet.state.mood, before)
        self.assertEqual(game.window.cget("bg"), "#8E9CB1")
        self.assertTrue(game.window.overrideredirect())
        self.assertIsNotNone(game._banner)
        for forbidden in ("score_label", "count_label", "remark_label",
                          "reveal_label"):
            self.assertFalse(hasattr(game, forbidden), forbidden)
        self.assertEqual(set(game.buttons), set(Move))
        self.assertIn("spielen", bubble_text(self.pet).lower())  # type: ignore[union-attr]
        self.pet._hover.dismiss_outside(-999, -999)
        self.assertIs(self.pet._hover.game_window, game)
        self.assertTrue(game.window.winfo_exists())
        toolbar.buttons["play"].invoke()
        self.assertIs(self.pet._hover.game_window, game)

    def test_character_bubble_says_every_phase_in_order(self) -> None:
        self.pet._hover.open_game()
        game = self.pet._hover.game_window
        assert game is not None
        game._sequence._game._random_index = lambda _size: 2
        game.choose(Move.ROCK)
        self.assertIn("Eins", bubble_text(self.pet))  # type: ignore[operator]
        self.assertEqual(game.score.games, 0)
        self.assertEqual(game.buttons[Move.ROCK].cget("state"), "disabled")
        game._sequence.advance()
        self.assertIn("Zwei", bubble_text(self.pet))  # type: ignore[operator]
        game._sequence.advance()
        self.assertIn("Drei", bubble_text(self.pet))  # type: ignore[operator]
        self.assertEqual(game.score.games, 0)
        game._sequence.advance()
        self.assertIn("✊🏻 Stein", bubble_text(self.pet))  # type: ignore[operator]
        self.assertIn("✌🏻 Schere", bubble_text(self.pet))  # type: ignore[operator]
        self.assertEqual(game.score.wins, 1)
        game._sequence.advance()
        self.assertIn("gewonnen", bubble_text(self.pet))  # type: ignore[operator]
        game._sequence.advance()
        self.assertIn("1 Runde", bubble_text(self.pet))  # type: ignore[operator]
        self.assertIn("Du hast 1 Siege", bubble_text(self.pet))  # type: ignore[operator]
        self.assertEqual(game.buttons[Move.ROCK].cget("state"), "disabled")
        game._sequence.advance()
        self.assertEqual(game.buttons[Move.ROCK].cget("state"), "normal")

    def test_game_mode_blocks_regular_care_and_autonomous_lines(self) -> None:
        self.pet._hover.open_game()
        self.pet._maybe_show_idle_emote(999999.0)
        self.pet._maybe_speak_spontaneously(999999.0)
        self.assertIn("spielen", bubble_text(self.pet).lower())  # type: ignore[union-attr]
        self.pet.state.affection = 15
        self.pet._hover._interact("pet")
        self.assertEqual(self.pet.state.affection, 15)
        self.pet._react_to_click(None)
        self.assertIsNotNone(self.pet._speech.bubble)

    def test_close_aborts_timer_clears_bubble_and_restarts_session(self) -> None:
        self.pet._hover.open_game()
        game = self.pet._hover.game_window
        assert game is not None
        game.choose(Move.PAPER)
        old_callback = game._sequence.advance
        self.assertIsNotNone(game._sequence.pending_timer)
        game.close()
        self.assertFalse(self.pet._hover.game_open)
        self.assertIsNone(self.pet._hover.game_window)
        self.assertIsNone(self.pet._speech.bubble)
        old_callback()
        self.assertIsNone(self.pet._speech.bubble)
        self.pet._hover.open_game()
        replacement = self.pet._hover.game_window
        assert replacement is not None
        self.assertIsNot(game, replacement)
        self.assertEqual(replacement.score.games, 0)

    def test_status_panel_play_uses_same_game_window(self) -> None:
        self.pet._hover.open_status()
        panel = self.pet._hover.status_panel
        assert panel is not None
        panel._actions.interact("play")
        self.assertTrue(self.pet._hover.game_open)
        game = self.pet._hover.game_window
        assert game is not None
        self.assertEqual(game.score.games, 0)


if __name__ == "__main__":
    unittest.main()
