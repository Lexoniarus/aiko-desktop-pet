"""Required object phase dialogue is complete, safe and names only known items."""

import unittest
from typing import get_args
from unittest.mock import patch

from aiko_pet.application.object_feedback import FeedbackKey, ObjectFeedback
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.pet.balance import parse_balance
from aiko_pet.pet.catalog_validation import load_json
from aiko_pet.pet.mind.catalog import CATALOGUE, DialogueBook, Line, Reaction
from aiko_pet.pet.mind.object_events import ObjectEvent
from aiko_pet.pet.mind.reaction_sequence import Cue
from aiko_pet.ui.pet_view.object_feedback_presenter import ObjectFeedbackPresenter
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from aiko_pet.ui.view_models.object_reactions import format_object_reaction


class ObjectReactionTests(unittest.TestCase):
    def test_early_loss_names_only_learned_identity(self):
        book = DialogueBook.from_file()
        items = load_item_catalog()
        lines = [line for line in book.lines if line.event == "object_place_missing"]
        self.assertGreaterEqual(len(lines), 3)
        for line in lines:
            reaction = Reaction(line.id, line.beats, line.animation, line.event)
            unknown = format_object_reaction(reaction, None, items).text
            known = format_object_reaction(reaction, "energy_drink", items).text
            self.assertIn("etwas", unknown)
            self.assertNotIn("Energy", unknown)
            self.assertIn("Energy", known)

    def test_offer_and_known_acceptance_copy_name_the_learned_item(self):
        book = DialogueBook.from_file()
        for line in book.lines:
            if line.event in ("object_offer", "object_refuse", "object_handover"):
                text = " ".join(beat.content or "" for beat in line.beats
                                if beat.kind == "text")
                self.assertIn("{item}", text, line.id)

    def test_object_playback_respects_configured_reading_time_after_formatting(self):
        raw = load_json(CATALOGUE.parent / "balance.json")
        raw["dialogue"]["minimum_text_ms"] = 3000
        delays = []
        player = ReactionPlayer(
            schedule=lambda delay, _callback: delays.append(delay) or "timer",
            cancel_timer=lambda _token: None,
            display_emote=lambda _text, _ms: None,
            display_text=lambda _text, _ms: None,
            start_action=lambda _clip, _duration: None,
            mark_spoken=lambda: None, is_closed=lambda: False,
        )
        presenter = ObjectFeedbackPresenter(player, load_item_catalog())
        with patch("aiko_pet.pet.mind.reaction_sequence.BALANCE", parse_balance(raw)):
            presenter.show(
                ObjectFeedback(FeedbackKey("test", 1), "object_recognized",
                               "object_1", "onigiri"),
                Reaction.spoken("id", "Das ist {item}.", "idle", "object_recognized"),
                lambda _receipt: None,
            )
        self.assertEqual(delays, [3000])

    def test_every_phase_event_has_unconditional_authored_copy(self):
        book = DialogueBook.from_file()
        for event in get_args(ObjectEvent):
            self.assertTrue(
                any(
                    line.event == event
                    and not line.moods
                    and not line.periods
                    and not line.weekdays
                    for line in book.lines
                ),
                event,
            )

    def test_formatter_uses_canonical_names_and_unknown_does_not_reveal_identity(self):
        items = load_item_catalog()
        reaction = Reaction(
            "id", (Cue.text("Das ist {item}."),), "idle", "object_recognized"
        )
        self.assertEqual(
            format_object_reaction(reaction, "onigiri", items).text, "Das ist Onigiri."
        )
        self.assertEqual(
            format_object_reaction(reaction, None, items).text, "Das ist etwas."
        )

    def test_object_templates_reject_attribute_access_and_format_expressions(self):
        for text in ("{item.secret}", "{other}", "{item!r}", "{item:100}"):
            with self.assertRaisesRegex(ValueError, "placeholder"):
                Line.parse(
                    dict(
                        id="one",
                        event="object_recognized",
                        beats=[dict(kind="text", content=text)],
                        animation="idle",
                        moods=[],
                        periods=[],
                        weekdays=[],
                    )
                )
