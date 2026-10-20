"""Actual matching food retires a wish and shares the existing reward pot."""

import unittest
from dataclasses import replace

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.consumption import ConsumptionOrigin
from aiko_pet.pet.friendship_history import FriendshipHistory, RelationshipEvent
from aiko_pet.pet.moodlets import MoodletId
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState

WALL = 1800000000.0


def food_pet(**values):
    return PetState(
        updated_at=WALL,
        lived_seconds=100,
        satiety=30,
        friendship=50,
        wishes=WishState(
            2,
            (
                ActiveWish(
                    1,
                    WishId.FOOD,
                    "apple",
                    0,
                    14400,
                ),
            ),
            ((WishArea.FOOD, 0),),
        ),
        **values,
    )


class FoodWishTests(unittest.TestCase):
    def test_unspoken_personal_intake_grants_ordinary_credit_before_wish_once(self):
        pet = food_pet()
        pet.restore_checkpoint(replace(pet.capture_checkpoint(), satiety=81))
        pet.consume_item("apple", ConsumptionOrigin.HANDOVER, now=WALL)
        self.assertFalse(pet.wishes.active)
        self.assertEqual(
            [e.kind for e in pet.friendship_history.rewards], ["feed", "wish"]
        )
        self.assertAlmostEqual(pet.friendship, 50.475)
        self.assertEqual(pet.moodlets.active[0].definition_id, MoodletId.FOOD_FULFILLED)
        self.assertEqual(pet.moodlets.active[0].remaining_seconds, 7200)
        loaded = decode_pet_state(encode_pet_state(pet), now=WALL)
        self.assertEqual(loaded.wishes, pet.wishes)
        self.assertEqual(loaded.friendship_history, pet.friendship_history)
        before = loaded.moodlets.active
        loaded.consume_item("apple", ConsumptionOrigin.HANDOVER, now=WALL)
        self.assertEqual(loaded.moodlets.active, before)
        self.assertAlmostEqual(loaded.friendship, 50.475)

    def test_autonomous_intake_has_impression_without_personal_credit(self):
        pet = food_pet()
        pet.consume_item("apple", ConsumptionOrigin.AUTONOMOUS, now=WALL)
        self.assertFalse(pet.wishes.active)
        self.assertEqual(pet.friendship, 50)
        self.assertFalse(pet.friendship_history.rewards)
        self.assertIsNone(pet.friendship_history.last_contact)
        self.assertEqual(pet.moodlets.active[0].definition_id, MoodletId.FOOD_FULFILLED)

    def test_wrong_food_rejection_and_deadline_do_not_fulfill(self):
        for target, satiety, elapsed in (
            ("cookie", 30, 100),
            ("apple", 100, 100),
            ("apple", 30, 14400),
        ):
            pet = food_pet()
            pet.restore_checkpoint(
                replace(
                    pet.capture_checkpoint(), satiety=satiety, lived_seconds=elapsed
                )
            )
            wishes = pet.wishes
            pet.consume_item(target, ConsumptionOrigin.HANDOVER, now=WALL)
            self.assertEqual(pet.wishes, wishes)
            self.assertFalse(pet.moodlets.active)

    def test_shared_cap_clips_bonus_but_never_blocks_impression(self):
        for used, expected in ((0.425, 0.1), (0.75, 0)):
            history = FriendshipHistory(
                0, rewards=(RelationshipEvent(90, "talk", used),)
            )
            pet = food_pet(relationship=history)
            pet.restore_checkpoint(replace(pet.capture_checkpoint(), satiety=81))
            pet.consume_item("apple", ConsumptionOrigin.HANDOVER, now=WALL)
            credits = pet.friendship_history.rewards
            bonus = sum(e.amount for e in credits if e.kind == "wish")
            self.assertAlmostEqual(bonus, expected)
            self.assertLessEqual(sum(e.amount for e in credits), 0.75)
            self.assertFalse(pet.wishes.active)
            self.assertEqual(pet.moodlets.active[0].level, 1)

    def test_ordinary_interval_does_not_suppress_independent_bonus(self):
        pet = food_pet(
            relationship=FriendshipHistory(
                0,
                eligible=(("feed", 90),),
            )
        )
        pet.consume_item("apple", ConsumptionOrigin.HANDOVER, now=WALL)
        self.assertEqual(pet.friendship_history.eligible, (("feed", 90),))
        self.assertAlmostEqual(pet.friendship, 50.25)
        self.assertEqual([e.kind for e in pet.friendship_history.rewards], ["wish"])

    def test_new_food_wish_refreshes_single_level_without_numeric_mood_jump(self):
        pet = food_pet()
        mood = pet.mood
        pet.consume_item("apple", ConsumptionOrigin.AUTONOMOUS, now=WALL)
        before = pet.moodlets.active[0]
        pet.restore_checkpoint(
            replace(
                pet.capture_checkpoint(),
                satiety=30,
                wishes=WishState(
                    3,
                    (ActiveWish(2, WishId.FOOD, "apple", 100, 14500),),
                    ((WishArea.FOOD, 100),),
                ),
            )
        )
        pet.consume_item("apple", ConsumptionOrigin.AUTONOMOUS, now=WALL)
        self.assertEqual(len(pet.moodlets.active), 1)
        self.assertEqual(pet.moodlets.active[0].instance_id, before.instance_id)
        self.assertEqual(pet.moodlets.active[0].level, 1)
        self.assertEqual(pet.mood, mood)
