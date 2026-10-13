"""Tk integration: only controls in input window; all cues use Aiko."""

from __future__ import annotations

import tempfile
import time
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
    children = frame.winfo_children()
    if not children or not isinstance(children[0], tk.Label):
        return None
    return str(children[0].cget("text"))


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

    def game(self) -> object:
        self.pet._hover.open_game()
        game = self.pet._hover.game_window
        assert game is not None
        return game

    def test_game_is_kenney_styled_input_only_and_stays_open(self) -> None:
        self.pet._on_enter()
        toolbar = self.pet._hover.toolbar
        assert toolbar is not None
        previous_mood = self.pet.state.mood
        toolbar.buttons["play"].invoke()
        game = self.pet._hover.game_window
        assert game is not None
        self.assertTrue(self.pet._hover.game_open)
        self.assertEqual(game.score.games, 0)
        self.assertEqual(self.pet.state.mood, previous_mood)
        self.assertEqual(game.window.cget("bg"), "#8E9CB1")
        self.assertTrue(game.window.overrideredirect())
        self.assertIsNotNone(game._banner)
        for forbidden in (
            "score_label", "count_label", "remark_label", "reveal_label",
        ):
            self.assertFalse(hasattr(game, forbidden), forbidden)
        self.assertEqual(set(game.buttons), set(Move))
        for move in Move:
            self.assertEqual(game.hand_images[move].width(), 72)
            self.assertIn("image", game.buttons[move].keys())
        welcome = bubble_text(self.pet)
        assert welcome is not None
        self.assertIn("Schere, Stein, Papier", welcome)
        self.pet._hover.dismiss_outside(-999, -999)
        self.assertIs(self.pet._hover.game_window, game)
        self.assertTrue(game.window.winfo_exists())
        toolbar.buttons["play"].invoke()
        self.assertIs(self.pet._hover.game_window, game)

    def test_character_bubble_emotes_animation_and_hands_are_sequential(self) -> None:
        self.pet._hover.open_game()
        game = self.pet._hover.game_window
        assert game is not None
        self.assertTrue(self.pet._animated._game_mode)
        self.assertEqual(
            self.pet._animated.frame_clock.active_key, ("waving", None),
        )
        game._sequence._game._random_index = lambda _size: 2
        game.choose(Move.ROCK)
        self.assertEqual(bubble_text(self.pet), "Eins!")
        self.assertEqual(game.score.games, 0)
        self.assertEqual(game.buttons[Move.ROCK].cget("state"), "disabled")
        game._sequence.advance()
        self.assertEqual(bubble_text(self.pet), "Zwei!")
        game._sequence.advance()
        self.assertEqual(bubble_text(self.pet), "Drei!")
        game._sequence.advance()
        self.assertIsNone(bubble_text(self.pet))
        self.assertIsNotNone(self.pet._speech.bubble)
        self.assertEqual(game.score.games, 0)
        game._sequence.advance()
        self.assertEqual(game.score.wins, 1)
        hand_bubble = self.pet._speech.bubble
        assert hand_bubble is not None
        self.assertEqual(len(self.pet._speech.game_hand_images), 2)
        self.assertEqual(
            {move: img.width() for move, img
             in self.pet._speech.game_hand_images.items()},
            {Move.ROCK: 72, Move.SCISSORS: 72},
        )
        game._sequence.advance()
        self.assertEqual(
            self.pet._animated.frame_clock.active_key, ("failed", None),
        )
        self.assertIsNone(bubble_text(self.pet))
        game._sequence.advance()
        line = bubble_text(self.pet)
        assert line is not None
        self.assertIn("Punkt", line)
        game._sequence.advance()
        score = bubble_text(self.pet)
        assert score is not None
        self.assertIn("1 Runde", score)
        self.assertIn("du 1, ich 0", score)
        self.assertEqual(game.buttons[Move.ROCK].cget("state"), "disabled")
        game._sequence.advance()
        self.assertEqual(game.buttons[Move.ROCK].cget("state"), "normal")

    def test_game_mode_freezes_pointer_following_without_changing_settings(self) -> None:
        self.pet._hover.open_game()
        pet_visual = self.pet._animated
        self.assertTrue(self.pet.settings.follow_cursor)
        self.assertIsNone(pet_visual.gaze_direction((99999, 99999)))
        self.assertIsNone(pet_visual.maybe_walk(time.monotonic(), 0.5))
        now = time.monotonic() + 5
        pet_visual.render(now, 0.14, (99999, 99999))
        active = pet_visual.frame_clock.active_key
        assert active is not None
        self.assertIn(active[0], ("waving", "waiting"))
        self.assertNotEqual(active[0], "look")
        self.pet._maybe_show_idle_emote(now)
        self.pet._maybe_speak_spontaneously(now)
        self.assertIsNotNone(self.pet._speech.bubble)
        self.pet._hover.close_game()
        self.assertFalse(pet_visual._game_mode)
        self.assertEqual(self.pet.settings.follow_cursor, True)
        self.assertIsNotNone(pet_visual.gaze_direction((99999, 99999)))

    def test_close_discards_pending_cues_and_restarts_session(self) -> None:
        self.pet._hover.open_game()
        game = self.pet._hover.game_window
        assert game is not None
        game.choose(Move.PAPER)
        stale = game._sequence.advance
        self.assertIsNotNone(game._sequence.pending_timer)
        game.close()
        self.assertFalse(self.pet._hover.game_open)
        self.assertFalse(self.pet._animated._game_mode)
        self.assertIsNone(self.pet._hover.game_window)
        self.assertIsNone(self.pet._speech.bubble)
        stale()
        self.assertIsNone(self.pet._speech.bubble)
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
        game = self.pet._hover.game_window
        assert game is not None
        self.assertEqual(game.score.games, 0)


if __name__ == "__main__":
    unittest.main()
