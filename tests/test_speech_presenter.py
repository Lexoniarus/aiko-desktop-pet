"""GUI regression tests for the independent speech and emote presenter."""

from __future__ import annotations

import tkinter as tk
import unittest

from aiko_pet.ui.speech_presenter import SpeechAnchor, SpeechPresenter
from aiko_pet.games.rock_paper_scissors import Move


class SpeechPresenterTests(unittest.TestCase):
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
            root=self.root,
            anchor=lambda: self.anchor,
            font_name="Segoe UI",
            always_on_top=lambda: False,
            restore_stack=lambda: self.restacks.append(True),
        )
        self.addCleanup(self.root.destroy)
        self.addCleanup(self.presenter.hide)

    def test_speech_is_rendered_as_plain_text_with_tail(self) -> None:
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
        self.assertEqual(bubble.winfo_children()[0].winfo_children()[0].cget(
            "text",
        ), "Nachher")
        self.assertFalse(bool(previous and previous.winfo_exists()))

    def test_game_hands_use_color_assets_in_the_same_character_bubble(
        self,
    ) -> None:
        self.presenter.show_game_hands(Move.ROCK, Move.PAPER, 2600)
        bubble = self.presenter.bubble
        assert bubble is not None
        self.assertEqual(len(bubble.winfo_children()), 2)
        self.assertEqual(set(self.presenter.game_hand_images), {
            Move.ROCK, Move.PAPER,
        })
        for image in self.presenter.game_hand_images.values():
            self.assertEqual(image.width(), 72)
        self.assertIsNotNone(self.presenter.pending_timer)
        self.presenter.show_text("Wieder normal", 2000)
        self.assertIsNotNone(self.presenter.bubble)

    def test_missing_emote_is_rejected_before_hiding_speech(self) -> None:
        self.presenter.show_text("Bleibt", 2000)
        old = self.presenter.bubble
        with self.assertRaises(ValueError):
            self.presenter.show_emote("invalid-emote")
        self.assertIs(self.presenter.bubble, old)


if __name__ == "__main__":
    unittest.main()
