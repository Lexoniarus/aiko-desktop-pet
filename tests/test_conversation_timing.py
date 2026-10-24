"""Social reading deadlines, final-text allowance and punchline ordering."""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path
from typing import Literal
from unittest.mock import Mock

from aiko_pet.application.social_content import (
    BUFFERED_CATEGORIES,
    SocialCategory,
    prepare_social_content,
)
from aiko_pet.pet.balance import parse_balance
from aiko_pet.pet.catalog_validation import load_json
from aiko_pet.pet.interaction_events import SocialCompletion
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.mind.reaction_sequence import Cue
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from tests.test_social_content import fact_payload, joke_payload
from tools.reaction_test_support import FakeScheduler

DATA = Path(__file__).resolve().parents[1] / "aiko_pet/data"


class ConversationTimingTests(unittest.TestCase):
    def test_clamp_boundaries_and_final_allowance_include_every_character(self):
        for length, ordinary, final in (
            (1, 4000, 5000), (38, 4000, 5000), (39, 4035, 5035),
            (40, 4100, 5100), (80, 6700, 7700), (115, 8975, 9975),
            (116, 9040, 10000), (125, 9625, 10000),
        ):
            with self.subTest(length=length):
                text = "A" + (" ,!?" * 31)[:length - 1]
                reaction = Reaction(
                    "timing", (Cue.text(text), Cue.text(text)), "idle", "talk",
                )
                self.assertEqual(
                    [cue.duration_ms for cue in reaction.beats], [ordinary, final],
                )

    def test_last_text_gets_allowance_before_trailing_emote_or_credit(self):
        reaction = Reaction(
            "sequence", (
                Cue.text("Inhalt."), Cue.text("Autor."),
                Cue("emote", "idea", 900), Cue("pause", "", 600),
            ), "idle", "talk", "story",
        )
        self.assertEqual([b.duration_ms for b in reaction.beats],
                         [4000, 5000, 900, 600])
        self.assertEqual(replace(reaction, wish_instance_id=7).beats, reaction.beats)
        single = Reaction.spoken("single", "Hallo.", "idle", "talk")
        self.assertEqual(single.beats[0].duration_ms, 5000)

    def test_other_feedback_keeps_existing_reading_timing(self):
        reaction = Reaction.spoken("contact", "Hallo.", "idle", "click_left")
        self.assertEqual(reaction.beats[0].duration_ms, 2800)
        self.assertEqual(Cue.text("x" * 125).duration_ms, 7250)

    def test_each_existing_social_format_receives_the_common_reading_policy(self):
        for category in BUFFERED_CATEGORIES:
            with self.subTest(category=category):
                payload = (fact_payload() if category == SocialCategory.FACT
                           else joke_payload(category))
                reaction = prepare_social_content(category, payload).reaction
                texts = [b for b in reaction.beats if b.kind == "text"]
                expected = [min(10000, max(4000, 1500 + len(b.content) * 65))
                            for b in texts]
                expected[-1] = min(10000, expected[-1] + 1000)
                self.assertEqual([b.duration_ms for b in texts], expected)

    def test_only_text_cues_allow_ten_seconds(self):
        self.assertEqual(Cue("text", "Lang.", 10000).duration_ms, 10000)
        invalid: tuple[tuple[Literal["text", "emote", "pause"], str, int], ...] = (
            ("text", "Lang.", 10001), ("emote", "idea", 8001),
            ("pause", "", 8001),
        )
        for kind, content, duration in invalid:
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                Cue(kind, content, duration)

    def test_invalid_conversation_balance_is_rejected(self):
        for key, value in (
            ("conversation_minimum_text_ms", 249),
            ("conversation_minimum_text_ms", 10001),
            ("conversation_maximum_text_ms", 3999),
            ("conversation_maximum_text_ms", 10001),
            ("conversation_orientation_ms", 10001),
            ("conversation_reading_ms_per_character", 0),
            ("conversation_final_text_ms", 10001),
            ("conversation_final_text_ms", -1),
            ("conversation_final_text_ms", True),
            ("conversation_punchline_pause_ms", 249),
            ("conversation_punchline_pause_ms", 8001),
        ):
            with self.subTest(key=key, value=value):
                raw = load_json(DATA / "balance.json")
                raw["dialogue"][key] = value
                with self.assertRaises(ValueError):
                    parse_balance(raw)


class SocialTimingPlaybackTests(unittest.TestCase):
    def setUp(self):
        self.scheduler = FakeScheduler()
        self.texts: list[tuple[str, int]] = []
        self.on_text = Mock()
        self.on_wish_text = Mock()
        self.social_completed = Mock()
        self.done = Mock()
        self.player = ReactionPlayer(
            schedule=self.scheduler.schedule, cancel_timer=self.scheduler.cancel,
            display_emote=lambda _text, _ms: None,
            display_text=lambda text, ms: self.texts.append((text, ms)),
            start_action=lambda _action, _duration: None,
            mark_spoken=lambda: None, is_closed=lambda: False,
            on_text=self.on_text, on_wish_text=self.on_wish_text,
            social_completed=self.social_completed,
        )
        payload = joke_payload(SocialCategory.TWO_PARTS)
        payload["setup"] = "Frage " * 35
        payload["delivery"] = "Antwort " * 25
        self.reaction = replace(
            prepare_social_content(SocialCategory.TWO_PARTS, payload).reaction,
            completed_social=SocialCompletion("twopart", 7), wish_instance_id=7,
        )

    def fire_next(self, expected_ms: int):
        token = self.player.pending_timer
        assert token is not None
        self.assertEqual(self.scheduler.callbacks[token][0], expected_ms)
        self.scheduler.fire(token)

    def test_full_setup_reading_precedes_one_pause_then_full_delivery(self):
        self.player.play(self.reaction, on_complete=self.done)
        for cue in self.reaction.beats:
            if cue.kind == "text":
                self.assertEqual(self.texts[-1], (cue.content, cue.duration_ms))
            if cue.kind == "pause":
                self.assertEqual(cue.duration_ms, 800)
                self.assertEqual(len(self.texts), 3)  # Intro + both setup bubbles.
            self.done.assert_not_called()
            self.fire_next(cue.duration_ms)
        self.assertEqual(sum(b.kind == "pause" for b in self.reaction.beats), 1)
        self.done.assert_called_once_with(True)
        self.on_text.assert_called_once_with("talk")
        self.on_wish_text.assert_called_once_with(7)
        self.social_completed.assert_called_once_with(SocialCompletion("twopart", 7))
        self.player.cancel()
        self.done.assert_called_once_with(True)
        self.social_completed.assert_called_once_with(SocialCompletion("twopart", 7))

    def test_reading_click_skips_punchline_pause_and_stale_callback(self):
        self.player.play(self.reaction, on_complete=self.done)
        pause_index = next(i for i, b in enumerate(self.reaction.beats)
                           if b.kind == "pause")
        for cue in self.reaction.beats[:pause_index]:
            self.fire_next(cue.duration_ms)
        token = self.player.pending_timer
        assert token is not None
        delay, stale = self.scheduler.callbacks[token]
        self.assertEqual(delay, 800)
        self.assertTrue(self.player.advance_story())
        current = self.player.pending_timer
        self.assertEqual(
            self.texts[-1][0], self.reaction.beats[pause_index + 1].content,
        )
        stale()
        self.assertEqual(self.player.pending_timer, current)
        self.player.cancel()
        self.done.assert_called_once_with(False)
        self.social_completed.assert_not_called()
