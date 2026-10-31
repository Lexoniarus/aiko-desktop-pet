"""Welcome-petting recollections do not grant consent or rewrite boundaries."""

import random
import unittest
from dataclasses import replace

from test_conversation_topics import actual
from test_everyday_experiences import pet_at
from test_wish_affection import wishes

from aiko_pet.pet.care_result import CareEffect
from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.mind.catalog import DialogueBook
from aiko_pet.pet.mind.conversation_topics import ConversationKind, ConversationTopic
from aiko_pet.pet.mind.dialogue_context import FriendshipStage
from aiko_pet.pet.moodlets import MoodletAttribution, MoodletCauseKind, MoodletId
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from tools.dialogue_test_support import dialogue_context
from tools.pet_test_support import require_test_value

WALL = 1800000000


def affection_context(
    cause, *, stage=FriendshipStage.FRIEND, emotion=EmotionalState.CALM
):
    return replace(
        dialogue_context(context_at(WALL), stage=stage),
        emotions=EmotionalComposition(emotion),
        conversation_topic=ConversationTopic(
            ConversationKind.AFFECTION,
            1,
            MoodletId.SECURE,
            cause,
        ),
    )


class PlaudernAffectionTests(unittest.TestCase):
    def setUp(self):
        self.book = DialogueBook.from_file(rng=random.Random(0))

    def test_full_need_qualifying_wish_has_four_relationship_bands_and_emotion_color(
        self,
    ):
        pet = PetState(
            updated_at=WALL,
            affection=100,
            friendship=0,
            lived_seconds=100,
            wishes=wishes(),
        )
        self.assertEqual(pet.interact("pet", now=WALL).effect, CareEffect.AFFECTION)
        self.assertEqual(pet.affection, 100)
        cause = pet.moodlets.active[0].causes[0]
        self.assertEqual(cause.kind, MoodletCauseKind.WISH_FULFILLED)
        checkpoint = pet.capture_checkpoint()
        normal = set()
        for stage in FriendshipStage:
            for emotion in (
                EmotionalState.CALM,
                EmotionalState.DOWNCAST,
                EmotionalState.AMBIVALENT,
            ):
                reaction = require_test_value(
                    self.book.choose(
                        "talk",
                        affection_context(cause, stage=stage, emotion=emotion),
                        10,
                    )
                )
                self.assertIn("personal-wish", reaction.line_id)
                text = " ".join(b.content for b in reaction.beats if b.kind == "text")
                self.assertIn("streichel", text.lower())
                self.assertNotIn("jederzeit", text)
                self.assertNotIn("immer streicheln", text)
                if emotion == EmotionalState.CALM:
                    normal.add(reaction.line_id)
                elif emotion == EmotionalState.AMBIVALENT:
                    self.assertIn("mixed", reaction.line_id)
                else:
                    self.assertIn("quiet", reaction.line_id)
        self.assertEqual(len(normal), 4)
        self.assertEqual(pet.capture_checkpoint(), checkpoint)
        # Telling the memory supplies no permission for the next excess contact.
        self.assertEqual(
            pet.interact("pet", now=WALL).effect, CareEffect.AFFECTION_ENOUGH
        )

    def test_welcome_gap_without_wish_does_not_invent_a_previous_desire(self):
        pet = pet_at(14400)
        pet.interact("pet", now=WALL)
        cause = pet.moodlets.active[0].causes[0]
        self.assertIsNone(cause.wish)
        reaction = require_test_value(
            self.book.choose("talk", affection_context(cause), 10)
        )
        self.assertIn("welcome", reaction.line_id)
        self.assertNotIn("gewünscht", " ".join(b.content for b in reaction.beats))

    def test_unknown_attribution_uses_wish_without_inventing_a_specific_giver(self):
        pet = PetState(
            updated_at=WALL,
            affection=20,
            friendship=50,
            lived_seconds=100,
            wishes=wishes(),
        )
        pet.interact("pet", now=WALL)
        cause = replace(
            pet.moodlets.active[0].causes[0], attribution=MoodletAttribution.UNKNOWN
        )
        reaction = require_test_value(
            self.book.choose("talk", affection_context(cause), 10)
        )
        self.assertIn("wanted-", reaction.line_id)
        text = " ".join(b.content for b in reaction.beats)
        self.assertNotIn("Du hast", text)
        self.assertNotIn("Danke", text)

    def test_unwelcome_contact_never_matches_a_welcome_affection_story(self):
        cause = actual(target="crowded")
        context = replace(
            affection_context(cause, stage=FriendshipStage.CLOSE),
            conversation_topic=ConversationTopic(
                ConversationKind.NEGATIVE,
                1,
                MoodletId.CROWDED,
                cause,
            ),
        )
        candidates = [
            line
            for line in self.book.lines
            if line.id.startswith("plaudern-affection-")
        ]
        self.assertTrue(candidates)
        self.assertFalse(any(line.matches(context) for line in candidates))


if __name__ == "__main__":
    unittest.main()
