"""Negative recollections preserve identity, attribution and modeled exposure."""

import random
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_conversation_topics import actual
from test_food_handover_wishes import pet_with
from test_plaudern import talk
from test_wish_assignment import wish

from aiko_pet.application.contact import acknowledge_interaction_text
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.pet.interaction_events import (
    ArrangementDisrupted,
    Poked,
    WithholdingObserved,
)
from aiko_pet.pet.mind.catalog import DialogueBook, Line
from aiko_pet.pet.mind.conversation_topics import (
    NEGATIVE_FAMILIES,
    POOR_CARE_FAMILIES,
    ConversationKind,
    ConversationTopic,
)
from aiko_pet.pet.mind.dialogue_context import FriendshipStage
from aiko_pet.pet.moodlets import MoodletAttribution, MoodletCauseKind, MoodletId
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import WishId
from tools.dialogue_test_support import dialogue_context
from tools.persistence_test_support import save_test_session
from tools.pet_test_support import require_test_value

WALL = 1800000000


def negative_context(
    family, cause, *, stage=FriendshipStage.FRIEND, emotion=EmotionalState.CALM
):
    kind = (
        ConversationKind.POOR_CARE
        if family in POOR_CARE_FAMILIES
        else ConversationKind.NEGATIVE
    )
    return replace(
        dialogue_context(context_at(WALL), stage=stage),
        emotions=EmotionalComposition(emotion),
        conversation_topic=ConversationTopic(kind, 1, family, cause),
    )


class PlaudernNegativeTests(unittest.TestCase):
    def setUp(self):
        self.book = DialogueBook.from_file(rng=random.Random(0))

    def choose(self, family, cause, **values):
        reaction = require_test_value(
            self.book.choose(
                "talk",
                negative_context(family, cause, **values),
                10,
                presentation="story",
            )
        )
        return reaction, " ".join(b.content for b in reaction.beats if b.kind == "text")

    def test_real_poking_cause_survives_restart_and_telling_cannot_erase_the_boundary(
        self,
    ):
        pet = PetState(updated_at=WALL, lived_seconds=100, friendship=90)
        acknowledge_interaction_text(pet, "click_boundary")
        pet.experience_interaction(Poked(True))
        cause = pet.moodlets.active[0].causes[0]
        snapshot = pet.capture_checkpoint()
        for stage in FriendshipStage:
            reaction, text = self.choose(MoodletId.POKING, cause, stage=stage)
            self.assertIn("poking-user", reaction.line_id)
            self.assertIn(
                "unangenehm"
                if stage in (FriendshipStage.ACQUAINTANCE, FriendshipStage.CLOSE)
                else "zu viel",
                text,
            )
        _, mixed = self.choose(
            MoodletId.POKING,
            cause,
            stage=FriendshipStage.CLOSE,
            emotion=EmotionalState.AMBIVALENT,
        )
        self.assertIn("trotzdem", mixed)
        self.assertEqual(pet.capture_checkpoint(), snapshot)
        with tempfile.TemporaryDirectory(prefix="aiko-negative-restart-") as folder:
            path = Path(folder) / "state.sqlite3"
            save_test_session(SqliteStateStore(path), pet, PetSettings())
            loaded = SqliteStateStore(path).load_session(now=WALL).state
            self.assertEqual(loaded.moodlets, pet.moodlets)
            self.assertIn("angestupst", talk(loaded).text)

    def test_unidentified_withheld_object_and_unknown_actor_never_acquire_a_food_name(
        self,
    ):
        pet = PetState(updated_at=WALL, lived_seconds=100)
        pet.experience_interaction(
            WithholdingObserved(
                incident_id="one",
                object_id="donut:still-unidentified",
            )
        )
        cause = pet.moodlets.active[0].causes[0]
        unknown = replace(cause, attribution=MoodletAttribution.UNKNOWN)
        reaction, text = self.choose(
            MoodletId.WITHHELD, unknown, stage=FriendshipStage.CLOSE
        )
        self.assertNotIn("-user-", reaction.line_id)
        self.assertIn("Ding", text)
        self.assertNotIn("Donut", text)
        self.assertNotIn("du hast", text.lower())
        self.assertNotIn("identifiziert", text)

    def test_search_retrospective_uses_its_own_cause_attribution(self):
        pet = PetState(updated_at=WALL, lived_seconds=100)
        pet.experience_interaction(ArrangementDisrupted(attributed=True))
        cause = pet.moodlets.active[0].causes[0]
        reaction, user_text = self.choose(MoodletId.DISRUPTED, cause)
        self.assertIn("disrupted-user", reaction.line_id)
        self.assertIn("gesucht", user_text)
        _, unknown_text = self.choose(
            MoodletId.DISRUPTED, replace(cause, attribution=MoodletAttribution.UNKNOWN)
        )
        self.assertIn("gesucht", unknown_text)
        self.assertNotIn("du hast", unknown_text.lower())

    def test_unwanted_handover_names_the_food_without_claiming_a_warning_or_intake(
        self,
    ):
        for expressed_at in (None, 0):
            pet = pet_with(
                replace(wish(WishId.AVOID_FOOD, "apple"), expressed_at=expressed_at)
            )
            pet.begin_food_handover("gift:1", object_id="portion:1")
            self.assertFalse(pet.moodlets.active)
            pet.recognize_food_handover("gift:1", "apple")
            self.assertEqual(pet.satiety, 100)
            cause = pet.moodlets.active[0].causes[0]
            _, text = self.choose(MoodletId.FOOD_WISH_DISREGARDED, cause)
            self.assertIn(DEFAULT_CATALOG.foods["apple"].display_name, text)
            for unsupported in ("gegessen", "gesagt", "gewarnt", "geschmeckt"):
                self.assertNotIn(unsupported, text)

    def test_all_incident_and_poor_care_families_have_grounded_stories_at_each_stage(
        self,
    ):
        for family in NEGATIVE_FAMILIES | POOR_CARE_FAMILIES:
            cause = actual(target=family.value)
            if family in POOR_CARE_FAMILIES:
                cause = replace(
                    cause,
                    kind=MoodletCauseKind.POOR_CARE,
                    attribution=MoodletAttribution.UNKNOWN,
                )
            for stage in FriendshipStage:
                reaction, text = self.choose(family, cause, stage=stage)
                self.assertTrue(reaction.line_id.startswith("plaudern-negative-"))
                if family in POOR_CARE_FAMILIES:
                    self.assertTrue("längere" in text or "Weile" in text)
                    self.assertNotIn("du hast", text.lower())
            reaction, _ = self.choose(family, cause, emotion=EmotionalState.AMBIVALENT)
            self.assertIn("mixed", reaction.line_id)

    def test_named_food_placeholder_requires_a_canonical_food_target_guard(self):
        raw = dict(
            id="bad-food",
            event="talk",
            animation="idle",
            presentation="story",
            periods=[],
            weekdays=[],
            beats=[dict(kind="text", content="{target}!")],
        )
        for targets in ([], ["pet"], ["blackjack", "apple"]):
            with self.subTest(targets=targets), self.assertRaises(ValueError):
                Line.parse(
                    dict(
                        raw,
                        conditions=[
                            dict(
                                conversation_topics=["negative.food_monotony"],
                                conversation_targets=targets,
                            )
                        ],
                    )
                )
        self.assertIsNotNone(
            Line.parse(
                dict(
                    raw,
                    conditions=[
                        dict(
                            conversation_topics=["negative.food_monotony"],
                            conversation_targets=["apple"],
                        )
                    ],
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
