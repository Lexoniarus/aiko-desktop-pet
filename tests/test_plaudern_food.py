"""Food stories respect intake, actual giver and the original preference."""

import random
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_conversation_topics import actual
from test_food_handover_wishes import pet_with
from test_plaudern import talk
from test_wish_assignment import wish
from test_wish_food import WALL, food_pet

from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.pet.consumption import ConsumptionOrigin
from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.pet.mind.catalog import DialogueBook
from aiko_pet.pet.mind.conversation_topics import ConversationKind, ConversationTopic
from aiko_pet.pet.mind.dialogue_context import FriendshipStage
from aiko_pet.pet.moodlets import MoodletAttribution, MoodletId, MoodletOutcome
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.wishes import WishId
from tools.dialogue_test_support import dialogue_context
from tools.persistence_test_support import save_test_session
from tools.pet_test_support import require_test_value


def choose_food(
    book, cause, *, stage=FriendshipStage.FRIEND, emotion=EmotionalState.CALM
):
    context = replace(
        dialogue_context(context_at(WALL), stage=stage),
        emotions=EmotionalComposition(emotion),
        conversation_topic=ConversationTopic(
            ConversationKind.FOOD,
            1,
            MoodletId.FOOD_FULFILLED,
            cause,
        ),
    )
    reaction = require_test_value(
        book.choose("talk", context, 10, presentation="story")
    )
    return reaction, " ".join(b.content for b in reaction.beats if b.kind == "text")


class PlaudernFoodTests(unittest.TestCase):
    def setUp(self):
        self.book = DialogueBook.from_file(rng=random.Random(0))

    def test_recognized_desired_handover_never_claims_eating_or_taste(self):
        pet = pet_with(wish(WishId.FOOD, "donut"))
        pet.begin_food_handover("gift:1", object_id="portion:1")
        self.assertFalse(pet.moodlets.active)
        pet.recognize_food_handover("gift:1", "donut")
        self.assertEqual(pet.satiety, 100)
        cause = pet.moodlets.active[0].causes[0]
        variants = set()
        for stage in FriendshipStage:
            for emotion in (
                EmotionalState.CALM,
                EmotionalState.DOWNCAST,
                EmotionalState.AMBIVALENT,
            ):
                reaction, text = choose_food(
                    self.book, cause, stage=stage, emotion=emotion
                )
                self.assertIn(DEFAULT_CATALOG.foods["donut"].display_name, text)
                self.assertNotIn("gegessen", text)
                self.assertNotIn("geschmeckt", text)
                self.assertNotIn("lecker", text)
                self.assertIn("desired-gift", reaction.line_id)
                variants.add(reaction.line_id)
        self.assertGreaterEqual(len(variants), 4)

    def test_autonomous_intake_keeps_desire_without_inventing_a_user_gift(self):
        pet = food_pet()
        pet.consume_item(
            "apple", ConsumptionOrigin.AUTONOMOUS, now=WALL, object_id="portion:1"
        )
        cause = pet.moodlets.active[0].causes[0]
        self.assertEqual(cause.attribution, MoodletAttribution.AUTONOMOUS)
        reaction, text = choose_food(self.book, cause)
        self.assertIn("desired-intake", reaction.line_id)
        self.assertIn(DEFAULT_CATALOG.foods["apple"].display_name, text)
        self.assertNotIn("gegeben", text)
        self.assertNotIn("Danke", text)
        self.assertNotIn("du hast", text.lower())
        with tempfile.TemporaryDirectory(prefix="aiko-plaudern-food-") as folder:
            path = Path(folder) / "state.sqlite3"
            save_test_session(SqliteStateStore(path), pet, PetSettings())
            loaded = SqliteStateStore(path).load_session(now=WALL).state
            self.assertEqual(loaded.moodlets, pet.moodlets)
            self.assertIn(
                DEFAULT_CATALOG.foods["apple"].display_name, talk(loaded).text
            )

    def test_positive_alternative_is_not_an_exact_desire_for_the_received_food(self):
        pet = pet_with(wish(WishId.AVOID_FOOD, "apple"))
        pet.begin_food_handover("gift:1", object_id="portion:1")
        pet.recognize_food_handover("gift:1", "cookie")
        cause = pet.moodlets.active[0].causes[0]
        reaction, text = choose_food(self.book, cause)
        self.assertIn("variety", reaction.line_id)
        self.assertIn(DEFAULT_CATALOG.foods["cookie"].display_name, text)
        self.assertNotIn("genau das Essen", text)
        self.assertNotIn("gegessen", text)
        self.assertNotIn("gesagt", text)

    def test_all_food_names_fit_real_bubbles_and_unknown_giver_never_gets_thanked(self):
        for target in DEFAULT_CATALOG.foods:
            for outcome in (MoodletOutcome.INTAKE, MoodletOutcome.HANDOVER):
                cause = replace(actual(target=target), outcome=outcome)
                reaction, text = choose_food(self.book, cause)
                self.assertIn(DEFAULT_CATALOG.foods[target].display_name, text)
                self.assertNotIn("Du hast", text)
                self.assertNotIn("Danke", text)
                self.assertTrue(
                    all(
                        len(b.content) <= 125
                        for b in reaction.beats
                        if b.kind == "text"
                    )
                )


if __name__ == "__main__":
    unittest.main()
