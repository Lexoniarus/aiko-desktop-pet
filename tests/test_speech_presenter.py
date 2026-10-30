"""Tk regression tests for Aiko's original speech and game-hand overlays."""

from __future__ import annotations

import tkinter as tk
import unittest

from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.ui.pet_view.speech_presenter import SpeechAnchor, SpeechPresenter


class SpeechPresenterTests(unittest.TestCase):
    def test_game_hand_survives_comment_and_emoji_expiry_but_not_game_close(self):
        self.presenter.begin_game()
        self.presenter.show_game_hand(Move.ROCK, 0)
        self.presenter.show_text("Schere, Stein, Papier!", 1800)
        self.assertEqual(self.presenter._game_hand, Move.ROCK)
        self.presenter.show_emote("star", 900)
        self.assertEqual(self.presenter._game_hand, Move.ROCK)
        self.presenter._expire()
        self.assertIsNotNone(self.presenter.bubble)
        self.assertEqual(self.presenter._game_hand, Move.ROCK)
        self.presenter.hide()
        self.assertIsNone(self.presenter.bubble)
        self.assertIsNone(self.presenter._game_hand)

    @classmethod
    def setUpClass(cls) -> None:
        try:
            window = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("Tk display unavailable") from error
        window.destroy()

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.anchor = SpeechAnchor(200, 500, 128)
        self.restacks: list[bool] = []
        self.presenter = SpeechPresenter(
            root=self.root, anchor=lambda: self.anchor,
            font_name="Segoe UI", always_on_top=lambda: False,
            restore_stack=lambda: self.restacks.append(True),
        )
        self.addCleanup(self.root.destroy)
        self.addCleanup(self.presenter.hide)

    def test_queued_old_expiry_cannot_remove_a_new_game_comment(self):
        self.presenter.begin_game()
        self.presenter.show_text("Die erste Ansage.", 1800)
        old = self.presenter.bubble
        assert old is not None
        self.presenter.show_emote("star", 900)
        current = self.presenter.bubble
        timer = self.presenter.pending_timer
        self.presenter._expire_current(old)
        self.assertIs(self.presenter.bubble, current)
        self.assertEqual(self.presenter.pending_timer, timer)

    def test_cursor_cue_is_nonblocking_and_cannot_replace_existing_speech(self):
        self.presenter.show_cursor_emote("question", 1500)
        self.assertIsNotNone(self.presenter.bubble)
        self.assertFalse(self.presenter.blocks_contact)
        self.presenter.hide()
        self.presenter.show_text("Geschichte", 6000)
        before = self.presenter.bubble
        self.presenter.show_cursor_emote("drops", 1500)
        self.assertIs(self.presenter.bubble, before)
        self.assertTrue(self.presenter.blocks_contact)
        self.presenter.hide()
        self.assertFalse(self.presenter.blocks_contact)

    def test_warning_reports_actual_vacant_slot_without_contact_lock(self):
        self.assertTrue(self.presenter.show_cursor_warning("Langsamer!", 2000))
        before = self.presenter.bubble
        self.assertFalse(self.presenter.blocks_contact)
        self.assertFalse(self.presenter.show_cursor_warning("Noch einmal", 2000))
        self.assertIs(before, self.presenter.bubble)
        self.presenter.hide()
        self.presenter.show_text("Geschichte", 6000)
        self.assertFalse(self.presenter.show_cursor_warning("Langsamer!", 2000))
        self.assertTrue(self.presenter.blocks_contact)

    def test_speech_renders_plain_text_with_existing_tail(self) -> None:
        self.presenter.show_text("Hallo <b>Browser</b>!", 6000)
        bubble = self.presenter.bubble
        assert bubble is not None
        self.assertEqual(len(bubble.winfo_children()), 2)
        frame = bubble.winfo_children()[0]
        self.assertEqual(
            frame.winfo_children()[0].cget("text"), "Hallo <b>Browser</b>!",
        )
        self.assertTrue(self.restacks)
        self.assertIsNotNone(self.presenter.pending_timer)
        self.presenter.hide()
        self.assertIsNone(self.presenter.bubble)
        self.assertIsNone(self.presenter.pending_timer)

    def test_new_speech_replaces_old_bubble_and_moves_with_anchor(self) -> None:
        self.presenter.show_text("Vorher", 6000)
        previous = self.presenter.bubble
        self.anchor = SpeechAnchor(360, 500, 128)
        self.presenter.show_text("Nachher", 6000)
        bubble = self.presenter.bubble
        assert bubble is not None
        self.assertIsNot(bubble, previous)
        self.assertEqual(
            bubble.winfo_children()[0].winfo_children()[0].cget("text"),
            "Nachher",
        )
        self.assertFalse(bool(previous and previous.winfo_exists()))

    def test_aikos_game_bubble_shows_only_her_hand(self) -> None:
        self.presenter.show_game_hand(Move.ROCK, 2600)
        bubble = self.presenter.bubble
        assert bubble is not None
        self.assertEqual(len(bubble.winfo_children()), 2)
        self.assertEqual(set(self.presenter.game_hand_images), {Move.ROCK})
        self.assertEqual(self.presenter.game_hand_images[Move.ROCK].width(), 64)
        frame = bubble.winfo_children()[0]
        panel = next(
            child for child in frame.winfo_children() if isinstance(child, tk.Frame)
        )
        labels = [
            str(child.cget("text")) for child in panel.winfo_children()
            if isinstance(child, tk.Label)
        ]
        self.assertIn("Ich nehme ...", labels)
        self.assertNotIn("Du", labels)
        self.assertIsNotNone(self.presenter.pending_timer)
        self.root.update_idletasks()
        position = bubble.winfo_geometry()
        self.anchor = SpeechAnchor(460, 500, 128)
        self.presenter.move()
        self.root.update_idletasks()
        self.assertNotEqual(bubble.winfo_geometry(), position)
        self.presenter.show_text("Wieder normal", 2000)
        self.assertIsNotNone(self.presenter.bubble)

    def test_missing_emote_does_not_hide_previous_speech(self) -> None:
        self.presenter.show_text("Bleibt", 2000)
        old = self.presenter.bubble
        with self.assertRaises(ValueError):
            self.presenter.show_emote("invalid-emote")
        self.assertIs(self.presenter.bubble, old)


if __name__ == "__main__":
    unittest.main()
