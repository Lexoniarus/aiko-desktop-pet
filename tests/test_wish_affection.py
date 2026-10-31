"""Petting wishes use accepted care, preserving boundaries and shared caps."""

import unittest
from dataclasses import replace

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.care_result import CareEffect
from aiko_pet.pet.friendship_history import FriendshipHistory
from aiko_pet.pet.moodlets import MoodletId
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState


def wishes(instance=1, created=0):
    return WishState(
        instance + 1,
        (
            ActiveWish(
                instance,
                WishId.PET,
                "pet",
                created,
                created + 14400,
            ),
        ),
        ((WishArea.AFFECTION, created),),
    )


class AffectionWishTests(unittest.TestCase):
    def test_accepted_unspoken_wish_at_low_mood_has_no_instant_bonus(self):
        pet = PetState(
            affection=10,
            mood=0,
            friendship=50,
            lived_seconds=100,
            wishes=wishes(),
            relationship=FriendshipHistory(
                0,
                eligible=(("pet", 90),),
            ),
        )
        result = pet.interact("pet", now=1800000000)
        self.assertEqual(result.effect, CareEffect.AFFECTION)
        self.assertFalse(pet.wishes.active)
        self.assertEqual(pet.moodlets.active[0].definition_id, MoodletId.SECURE)
        self.assertEqual(pet.mood, 0)
        self.assertAlmostEqual(pet.friendship, 50)
        pet.interact("pet", now=1800000001)
        self.assertEqual(pet.moodlets.active[0].level, 1)
        self.assertEqual(len(pet.friendship_history.rewards), 0)

    def test_rejected_petting_never_fulfills_or_overrides_a_boundary(self):
        pet = PetState(affection=100, friendship=0, lived_seconds=100)
        pet.interact("pet", now=1800000000)
        pet.interact("pet", now=1800000000)
        pet.restore_checkpoint(replace(
            pet.capture_checkpoint(), wishes=wishes(), moodlets=replace(
                pet.moodlets, interactions=replace(pet.moodlets.interactions,
                                                  petting_refused_until=1000),
            ),
        ))
        history = pet.friendship_history
        result = pet.interact("pet", now=1800000000)
        self.assertEqual(result.effect, CareEffect.AFFECTION_REFUSED)
        self.assertEqual(pet.wishes, wishes())
        self.assertFalse(pet.moodlets.active)
        self.assertEqual(pet.friendship_history, history)

    def test_accepted_extra_stroke_can_fulfill_pinned_wish_without_another_desire(self):
        pinned = replace(wishes(), active=(replace(wishes().active[0], pinned=True),))
        pet = PetState(affection=100, friendship=50, lived_seconds=100, wishes=pinned)
        self.assertEqual(pet.interact("pet").effect, CareEffect.AFFECTION)
        self.assertFalse(pet.wishes.active)
        self.assertEqual(pet.moodlets.active[0].definition_id, MoodletId.SECURE)

    def test_distinct_wishes_stack_security_then_extend_each_existing_tier(self):
        pet = PetState(affection=10, friendship=50, lived_seconds=100, wishes=wishes())
        pet.interact("pet", now=1800000000)
        episode = pet.moodlets.active[0].instance_id
        for instance in (2, 3, 4):
            pet.restore_checkpoint(
                replace(
                    pet.capture_checkpoint(), affection=10, wishes=wishes(instance, 100)
                )
            )
            pet.interact("pet", now=1800000000)
        self.assertEqual(len(pet.moodlets.active), 1)
        self.assertEqual(pet.moodlets.active[0].instance_id, episode)
        self.assertEqual(pet.moodlets.active[0].level, 3)
        self.assertEqual(pet.moodlets.active[0].remaining_seconds, 3300)
        self.assertLessEqual(
            sum(e.amount for e in pet.friendship_history.rewards), 0.75
        )

    def test_full_need_wish_is_welcome_without_excess_and_permission_is_one_use(self):
        pet = PetState(affection=100, friendship=0, lived_seconds=100,
                       wishes=wishes())
        memory = pet.moodlets.interactions
        result = pet.interact("pet", now=1800000000)
        self.assertEqual(result.effect, CareEffect.AFFECTION)
        self.assertEqual(pet.affection, 100)
        self.assertEqual(pet.moodlets.interactions, memory)
        self.assertFalse(pet.wishes.active)
        self.assertEqual(pet.moodlets.active[0].definition_id, MoodletId.SECURE)
        pet = decode_pet_state(encode_pet_state(pet), now=1800000000)
        self.assertEqual(pet.interact("pet", now=1800000000).effect,
                         CareEffect.AFFECTION_ENOUGH)
        self.assertEqual(pet.moodlets.interactions.petting_excess_attempts, 1)
        self.assertEqual(pet.moodlets.active[0].level, 1)

    def test_expired_wish_does_not_bypass_full_need_tolerance(self):
        pet = PetState(affection=100, friendship=0, lived_seconds=14400,
                       wishes=wishes())
        self.assertEqual(pet.interact("pet", now=1800000000).effect,
                         CareEffect.AFFECTION_ENOUGH)
        self.assertFalse(pet.moodlets.active)
