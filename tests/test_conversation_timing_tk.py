"""Native Windows/Tk speech visibility at controlled social reading deadlines."""

from __future__ import annotations

import tkinter as tk
import unittest
from dataclasses import replace

from aiko_pet.application.social_content import SocialCategory, prepare_social_content
from aiko_pet.pet.mind.catalog import DialogueBook, Reaction
from aiko_pet.pet.mind.reaction_sequence import Cue
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from aiko_pet.ui.pet_view.speech_presenter import SpeechAnchor, SpeechPresenter
from tests.test_social_content import fact_payload, joke_payload
from tools.tk_test_time import ControlledTkTime


class ConversationTimingTkTests(unittest.TestCase):
    def setUp(self):
        self.clock = ControlledTkTime()
        self.clock.__enter__()
        self.addCleanup(self.clock.__exit__, None, None, None)
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"Tk display unavailable: {error}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.presenter = SpeechPresenter(
            root=self.root, anchor=lambda: SpeechAnchor(200, 500, 128),
            font_name="Segoe UI", always_on_top=lambda: False,
            restore_stack=lambda: None,
        )
        self.addCleanup(self.presenter.hide)
        self.player = ReactionPlayer(
            schedule=self.root.after, cancel_timer=self.root.after_cancel,
            display_emote=self.presenter.show_emote,
            display_text=self.presenter.show_text,
            start_action=lambda _action, _duration: None,
            mark_spoken=lambda: None, is_closed=lambda: False,
            hide_speech=self.presenter.hide,
        )
        self.addCleanup(self.player.cancel)

    def test_all_four_actions_keep_native_bubbles_until_their_full_deadline(self):
        reactions = []
        for category in SocialCategory:
            payload = (fact_payload() if category == SocialCategory.FACT
                       else joke_payload(category))
            reactions.append(prepare_social_content(category, payload).reaction)
        line = next(line for line in DialogueBook.from_file().lines
                    if line.event == "talk" and line.presentation == "story")
        reactions.append(Reaction(line.id, line.beats, "idle", "talk", "story"))
        # Exercise native hiding at the short, medium and 125-character limits too.
        for length in (40, 80, 125):
            text = ("Ein lesbarer Text. " * 8)[:length - 1] + "."
            reactions.append(Reaction.spoken(str(length), text, "idle", "talk"))
        for reaction in reactions:
            with self.subTest(line_id=reaction.line_id):
                self.player.play(reaction)
                for cue in reaction.beats:
                    self.clock.advance((cue.duration_ms - 1) / 1000)
                    bubble = self.presenter.bubble
                    if cue.kind == "pause":
                        self.assertIsNone(bubble)
                    else:
                        assert bubble is not None
                        self.assertTrue(bubble.winfo_ismapped())
                        if cue.kind == "text":
                            self.assertEqual(
                                bubble.winfo_children()[0].winfo_children()[0]
                                .cget("text"), cue.content,
                            )
                    self.clock.advance(0.001)
                self.assertFalse(self.player.active)
                self.assertIsNone(self.presenter.bubble)
                self.assertIsNone(self.presenter.pending_timer)

    def test_final_bonus_stays_visible_before_emote_and_reading_can_skip_pause(self):
        reaction = Reaction(
            "native", (
                Cue.text("Frage?"), Cue("pause", "", 800),
                Cue.text("Pointe!"), Cue("emote", "faceHappy", 900),
            ), "idle", "talk", "story",
        )
        self.player.play(reaction)
        self.clock.advance(4)
        self.assertIsNone(self.presenter.bubble)
        self.clock.advance(0.799)
        self.assertIsNone(self.presenter.bubble)
        self.clock.advance(0.001)
        final_bubble = self.presenter.bubble
        self.clock.advance(4.999)
        self.assertIs(self.presenter.bubble, final_bubble)
        assert final_bubble is not None
        self.assertTrue(final_bubble.winfo_ismapped())
        self.clock.advance(0.001)
        self.assertIsNot(self.presenter.bubble, final_bubble)
        self.assertFalse(final_bubble.winfo_exists())
        self.clock.advance(0.9)
        self.assertFalse(self.player.active)

        # A click during the pause starts the punchline immediately. Its timer
        # must survive the old pause deadline and cancellation must hide it.
        self.player.play(replace(reaction, line_id="reading-click"))
        self.clock.advance(4)
        self.assertTrue(self.player.advance_story())
        current = self.presenter.bubble
        self.clock.advance(0.8)
        self.assertIs(self.presenter.bubble, current)
        self.player.cancel()
        self.clock.advance(10)
        self.assertIsNone(self.presenter.bubble)
        self.assertFalse(self.player.active)
