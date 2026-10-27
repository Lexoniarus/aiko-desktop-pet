"""Tk checks for Aiko's bubble, the player's hand, and round counters."""

from __future__ import annotations

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.games.contracts import GameId
from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.windows.rock_paper_scissors_window import RockPaperScissorsWindow
from tools.desktop_test_support import create_test_desktop
from tools.tk_test_time import ControlledTkTime


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
        self.timing = self.enterContext(ControlledTkTime())
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pet = create_test_desktop(
            store=StateStore(Path(folder.name) / "save.json"),
        )
        self.addCleanup(self.pet.quit)
        self.pet.settings.auto_routine = False
        self.pet.settings.spontaneous_talk = False

    def test_game_window_has_player_hand_and_transient_score(self) -> None:
        self.pet._hover.show_toolbar()
        toolbar = self.pet._hover.toolbar
        assert toolbar is not None
        previous_mood = self.pet.state.mood
        toolbar.buttons["play"].invoke()
        menu = self.pet._hover.game_menu
        assert menu is not None
        menu.choose(GameId.ROCK_PAPER_SCISSORS)
        game = self.pet._hover.game_window
        assert isinstance(game, RockPaperScissorsWindow)
        self.assertTrue(self.pet._hover.game_open)
        self.assertEqual(game.window.cget("bg"), game.skin.border)
        self.assertTrue(game.window.overrideredirect())
        self.assertEqual(game.score.games, 0)
        self.assertEqual(self.pet.state.mood, previous_mood)
        for forbidden in ("count_label", "remark_label", "reveal_label"):
            self.assertFalse(hasattr(game, forbidden))
        self.assertEqual(set(game.buttons), set(Move))
        self.assertEqual(
            set(game.score_labels),
            {
                "games",
                "wins",
                "losses",
                "draws",
            },
        )
        for count in game.score_labels.values():
            self.assertEqual(count.cget("text"), "0")
        self.assertEqual(
            game.player_hand.itemcget(game._hand_image_item, "state"),
            "hidden",
        )
        for move in Move:
            self.assertEqual(game.hand_images[move].width(), 96)
            self.assertIs(
                game.hand_images[move],
                game.skin.images.icon(f"play_rps_{move.value}", 96),
            )
        self.pet._hover.dismiss_outside(-999, -999)
        self.assertIs(self.pet._hover.game_window, game)
        self.assertTrue(game.window.winfo_exists())
        self.assertEqual(toolbar.buttons["play"].cget("state"), "normal")
        with (
            patch.object(game, "focus") as focus,
            patch("aiko_pet.ui.windows.hover_ui.RockPaperScissorsWindow") as create,
        ):
            toolbar.buttons["play"].invoke()
            self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        focus.assert_not_called()
        create.assert_not_called()
        self.assertIsNone(self.pet._hover.game_menu)
        self.assertIs(self.pet._hover.game_window, game)

    def test_system_close_cancels_pending_round_and_releases_game_mode(self):
        before = self.pet.state.fun
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        game = self.pet._hover.game_window
        assert isinstance(game, RockPaperScissorsWindow)
        game.choose(Move.ROCK)
        pending = game._sequence.pending_timer
        assert pending is not None
        self.pet.root.tk.eval(game.window.protocol("WM_DELETE_WINDOW"))
        game._sequence.advance()
        game.close()
        self.assertNotIn(pending, self.pet.root.tk.call("after", "info"))
        self.assertIsNone(game._sequence.pending_timer)
        self.assertFalse(game.window.winfo_exists())
        self.assertIsNone(self.pet._hover.game_window)
        self.assertFalse(self.pet._animated.game_mode)
        self.assertIsNone(self.pet._speech.bubble)
        self.assertEqual(self.pet.state.fun, before)

    def test_player_and_aiko_reveal_separately_and_update_ui(self) -> None:
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        game = self.pet._hover.game_window
        assert isinstance(game, RockPaperScissorsWindow)
        self.assertTrue(self.pet._animated._game_mode)
        self.assertEqual(
            self.pet._animated.frame_clock.active_key,
            ("waving-greeting", None),
        )
        game._sequence._game._random_index = lambda _size: 2
        game.choose(Move.ROCK)
        self.assertEqual(bubble_text(self.pet), "Eins!")
        self.assertEqual(game.score.games, 0)
        self.assertEqual(game.score_labels["games"].cget("text"), "0")
        self.assertEqual(
            game.player_hand.itemcget(game._hand_image_item, "state"),
            "hidden",
        )
        self.assertEqual(game.buttons[Move.ROCK].cget("state"), "disabled")
        game._sequence.advance()
        self.assertEqual(bubble_text(self.pet), "Zwei!")
        game._sequence.advance()
        self.assertEqual(bubble_text(self.pet), "Drei!")
        game._sequence.advance()
        self.assertIsNone(bubble_text(self.pet))
        self.assertEqual(game.score.games, 0)
        game._sequence.advance()
        self.assertEqual(game.score.wins, 1)
        self.assertEqual(game.player_result_label.cget("text"), "Du: Stein")
        self.assertEqual(
            game.player_hand.itemcget(game._hand_image_item, "image"),
            str(game.hand_images[Move.ROCK]),
        )
        self.assertEqual(
            game.player_hand.itemcget(game._hand_image_item, "state"),
            "normal",
        )
        self.assertEqual(game.score_labels["games"].cget("text"), "1")
        self.assertEqual(game.score_labels["wins"].cget("text"), "1")
        self.assertEqual(game.score_labels["losses"].cget("text"), "0")
        self.assertEqual(game.score_labels["draws"].cget("text"), "0")
        self.assertEqual(
            set(self.pet._speech.game_hand_images),
            {
                Move.SCISSORS,
            },
        )
        # Aiko's speech frame shows her own hand, not the player's image.
        self.assertNotEqual(
            self.pet._speech.game_hand_images[Move.SCISSORS],
            game.hand_images[Move.ROCK],
        )
        self.assertIsNone(bubble_text(self.pet))
        game._sequence.advance()
        self.assertEqual(
            self.pet._animated.frame_clock.active_key,
            ("failed", None),
        )
        game._sequence.advance()
        remark = bubble_text(self.pet)
        assert remark is not None
        from aiko_pet.pet.mind.catalog import DialogueBook

        self.assertIn(
            remark,
            {
                line.text
                for line in DialogueBook.from_file().lines
                if line.event == "game_player_win"
            },
        )
        self.assertNotIn("Unser Stand", remark)
        game._sequence.advance()
        self.assertEqual(game.buttons[Move.ROCK].cget("state"), "normal")
        self.assertEqual(game.score.games, 1)

    def test_second_round_replaces_highlight_not_score(self) -> None:
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        game = self.pet._hover.game_window
        assert isinstance(game, RockPaperScissorsWindow)
        game._sequence._game._random_index = lambda _size: 0
        game.choose(Move.ROCK)
        for _ in range(7):
            game._sequence.advance()
        self.assertEqual(game.score.games, 1)
        game.choose(Move.PAPER)
        self.assertEqual(
            game.player_hand.itemcget(game._hand_image_item, "image"),
            str(game.hand_images[Move.ROCK]),
        )
        self.assertEqual(
            game.player_result_label.cget("text"),
            "Letzte Hand: Stein",
        )
        self.assertEqual(game.score_labels["games"].cget("text"), "1")
        for _ in range(4):
            game._sequence.advance()
        self.assertEqual(game.score_labels["games"].cget("text"), "2")
        self.assertEqual(game.score_labels["wins"].cget("text"), "1")
        self.assertEqual(game.score_labels["draws"].cget("text"), "1")

    def test_player_hand_cannot_shrink_or_clip_after_any_selection(self) -> None:
        """Window size and canvas pixels remain fixed for the entire session."""
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        game = self.pet._hover.game_window
        assert isinstance(game, RockPaperScissorsWindow)
        # Windows delivers native visibility/layout events after idle work.
        # Measure realized pixels, not the pre-map 1x1 child placeholders.
        game.window.wait_visibility()
        game.window.update_idletasks()
        dimensions = (game.window.winfo_width(), game.window.winfo_height())
        slot = (game.player_hand.winfo_width(), game.player_hand.winfo_height())
        self.assertEqual(slot, (120, 96))

        for move in (Move.ROCK, Move.PAPER, Move.SCISSORS):
            game.choose(move)
            game.window.update_idletasks()
            self.assertEqual(
                (game.window.winfo_width(), game.window.winfo_height()),
                dimensions,
            )
            for _ in range(4):
                game._sequence.advance()
            game.window.update_idletasks()
            bounds = game.player_hand.bbox(game._hand_image_item)
            assert bounds is not None
            left, top, right, bottom = bounds
            self.assertGreaterEqual(left, 0)
            self.assertGreaterEqual(top, 0)
            self.assertEqual((right - left, bottom - top), (96, 96))
            self.assertLessEqual(right, slot[0])
            self.assertLessEqual(bottom, slot[1])
            self.assertEqual(
                (game.window.winfo_width(), game.window.winfo_height()),
                dimensions,
            )
            for _ in range(3):
                game._sequence.advance()
            self.assertEqual(game.buttons[move].cget("state"), "normal")

    def test_cursor_tracking_stays_paused_during_game(self) -> None:
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        visual = self.pet._animated
        self.assertTrue(self.pet.settings.follow_cursor)
        self.assertIsNone(
            self.pet._visual.gaze_direction((99999, 99999), game_mode=visual.game_mode)
        )
        self.assertIsNone(
            self.pet._walk.step(
                time.monotonic(),
                0.5,
                game_mode=visual.game_mode,
                attention_active=False,
            )
        )
        visual.render(time.monotonic() + 5, (99999, 99999))
        current = visual.frame_clock.active_key
        assert current is not None
        self.assertIn(current[0], ("waving-greeting", "waiting"))
        with patch.object(
            visual, "cancel_action", wraps=visual.cancel_action,
        ) as cancel:
            self.pet._hover.close_game()
        cancel.assert_called_once()
        self.assertFalse(visual._game_mode)
        self.assertLessEqual(self.pet._action_playback.until, time.monotonic())
        # Closing a game resets interest. Fresh nearby input restores it.
        now = time.monotonic()
        eyes = visual.cursor_eye_position
        pointer = (round(eyes[0] + 180), round(eyes[1]))
        for sample_time in (now, now + 0.14):
            self.pet._cursor_observation.observe(
                pointer, sample_time, game_mode=False, eyes=eyes,
                screen_width=1920, scale=self.pet.settings.scale,
            )
            self.pet._pointer_runtime.begin_behaviour(sample_time)
        self.assertIsNotNone(
            self.pet._visual.gaze_direction(pointer, game_mode=visual.game_mode)
        )

    def test_close_cancels_outstanding_bubble_and_session(self) -> None:
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        game = self.pet._hover.game_window
        assert isinstance(game, RockPaperScissorsWindow)
        game.choose(Move.PAPER)
        stale = game._sequence.advance
        self.assertIsNotNone(game._sequence.pending_timer)
        game.close()
        self.assertFalse(self.pet._hover.game_open)
        self.assertIsNone(self.pet._hover.game_window)
        self.assertIsNone(self.pet._speech.bubble)
        stale()
        self.assertIsNone(self.pet._speech.bubble)
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        replacement = self.pet._hover.game_window
        assert isinstance(replacement, RockPaperScissorsWindow)
        self.assertIsNot(game, replacement)
        self.assertEqual(replacement.score.games, 0)
        self.assertEqual(replacement.score_labels["games"].cget("text"), "0")

    def test_completed_round_awards_fun_once_when_window_closes(self) -> None:
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        game = self.pet._hover.game_window
        assert isinstance(game, RockPaperScissorsWindow)
        before = self.pet.state.fun
        game._sequence._game._random_index = lambda _size: 2
        game.choose(Move.ROCK)
        for _ in range(4):
            game._sequence.advance()
        self.assertEqual(game.score.games, 1)
        self.assertEqual(self.pet.state.fun, before)
        game.close()
        awarded = self.pet.state.fun
        self.assertGreater(awarded, before)
        game.close()
        self.assertEqual(self.pet.state.fun, awarded)
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        again = self.pet._hover.game_window
        assert isinstance(again, RockPaperScissorsWindow)
        self.assertEqual(again.score.games, 0)
        self.assertEqual(self.pet.state.fun, awarded)

    def test_unrevealed_round_and_empty_window_give_no_fun(self) -> None:
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        empty = self.pet._hover.game_window
        assert isinstance(empty, RockPaperScissorsWindow)
        before = self.pet.state.fun
        empty.close()
        self.assertEqual(self.pet.state.fun, before)
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        pending = self.pet._hover.game_window
        assert isinstance(pending, RockPaperScissorsWindow)
        pending.choose(Move.PAPER)
        pending.close()
        self.assertEqual(self.pet.state.fun, before)

    def test_pinned_toolbar_play_uses_same_window(self) -> None:
        self.pet._hover.open_status()
        panel = self.pet._hover.toolbar
        assert panel is not None
        panel.buttons["play"].invoke()
        menu = self.pet._hover.game_menu
        assert menu is not None
        menu.choose(GameId.ROCK_PAPER_SCISSORS)
        self.assertTrue(self.pet._hover.game_open)
        game = self.pet._hover.game_window
        assert isinstance(game, RockPaperScissorsWindow)
        self.assertEqual(game.score.games, 0)


if __name__ == "__main__":
    unittest.main()
