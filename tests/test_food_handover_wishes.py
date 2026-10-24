"""Frozen handover context resolves once on recognition, separately from nutrition."""

import unittest
from dataclasses import replace

from test_wish_assignment import wish

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.food_handover import HandoverStatus
from aiko_pet.pet.food_wishes import food_wish_permission
from aiko_pet.pet.moodlets import MoodletAttribution, MoodletId, MoodletOutcome
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import WishArea, WishId, WishState
from tools.pet_test_support import require_test_value


def pet_with(*wishes):
    return PetState(lived_seconds=100, satiety=100, friendship=50,
                    wishes=WishState(max(w.instance_id for w in wishes) + 1,
                                     wishes, ((WishArea.FOOD, 0),), refresh_at=600))


class FoodHandoverWishTests(unittest.TestCase):
    def test_desired_handover_waits_for_recognition_without_nutrition(self):
        pet = pet_with(wish(WishId.FOOD, "apple"))
        needs, food, contact = pet.needs, pet.food, pet.friendship_history
        pet.begin_food_handover("gift:1", object_id="object_1")
        self.assertFalse(pet.moodlets.active)
        self.assertTrue(pet.wishes.active)
        pet = decode_pet_state(encode_pet_state(pet), now=1800000000)
        pet.restore_checkpoint(replace(pet.capture_checkpoint(), lived_seconds=120))
        pet.recognize_food_handover("gift:1", "apple")
        self.assertFalse(pet.wishes.active)
        self.assertEqual((pet.needs, pet.food, pet.friendship_history),
                         (needs, food, contact))
        episode = pet.moodlets.active[0]
        self.assertEqual((episode.definition_id, episode.remaining_seconds),
                         (MoodletId.FOOD_FULFILLED, 3600))
        cause = episode.causes[0]
        self.assertEqual((cause.occurred_at, cause.handed_over_at), (120, 100))
        self.assertEqual(cause.attribution, MoodletAttribution.USER)
        self.assertEqual(cause.outcome, MoodletOutcome.HANDOVER)
        pet = decode_pet_state(encode_pet_state(pet), now=1800000000)
        before = pet.capture_checkpoint()
        pet.recognize_food_handover("gift:1", "apple")
        pet.begin_food_handover("gift:1", object_id="object_1")
        self.assertEqual(pet.capture_checkpoint(), before)

    def test_unwanted_food_overrides_competing_positive_pin_without_eating(self):
        pet = pet_with(wish(WishId.AVOID_FOOD, "apple"),
                       wish(WishId.FOOD, "apple", instance=2, pinned=True))
        pet.begin_food_handover("gift:1", object_id="object_1")
        pet.recognize_food_handover("gift:1", "apple")
        self.assertEqual([w.instance_id for w in pet.wishes.active], [2])
        episode = pet.moodlets.active[0]
        self.assertEqual((episode.definition_id, episode.remaining_seconds),
                         (MoodletId.FOOD_WISH_DISREGARDED, 1800))
        self.assertEqual(pet.satiety, 100)
        self.assertEqual(pet.friendship, 50)
        permission = food_wish_permission(
            pet.wishes, "apple", object_id="object_1", elapsed=100,
            definitions=WISH_CATALOG.definitions,
        )
        self.assertTrue(permission.excluded)
        self.assertFalse(permission.requested)
        loaded = decode_pet_state(encode_pet_state(pet), now=1800000000)
        self.assertEqual(loaded.moodlets, pet.moodlets)

    def test_alternative_food_fulfills_variety_and_wrong_ordinary_food_is_neutral(self):
        for key, success in ((WishId.AVOID_FOOD, True), (WishId.FOOD, False)):
            with self.subTest(key=key):
                pet = pet_with(wish(key, "apple"))
                pet.begin_food_handover("gift:1", object_id="object_1")
                pet.recognize_food_handover("gift:1", "cookie")
                self.assertEqual(bool(pet.moodlets.active), success)
                self.assertEqual(bool(pet.wishes.active), not success)
                self.assertEqual(pet.wishes.food_handovers[0].status,
                                 HandoverStatus.EVALUATED)

    def test_frozen_context_survives_rotation_and_never_adopts_new_wishes(self):
        pet = pet_with(wish(WishId.FOOD, "apple"))
        pet.begin_food_handover("gift:1", object_id="object_1")
        later = wish(WishId.FOOD, "apple", instance=2, at=700)
        pet.restore_checkpoint(replace(
            pet.capture_checkpoint(), lived_seconds=700,
            wishes=replace(pet.wishes, active=(later,), next_instance_id=3,
                           last_created_by_area=((WishArea.FOOD, 700),)),
        ))
        pet.recognize_food_handover("gift:1", "apple")
        self.assertEqual(pet.wishes.active, (later,))
        self.assertEqual(
            require_test_value(pet.moodlets.active[0].causes[0].wish).instance_id, 1
        )

    def test_two_actual_gifts_cannot_settle_the_same_original_wish_twice(self):
        pet = pet_with(wish(WishId.FOOD, "apple"))
        pet.begin_food_handover("gift:1", object_id="object_1")
        pet.begin_food_handover("gift:2", object_id="object_2")
        pet.recognize_food_handover("gift:1", "apple")
        pet = decode_pet_state(encode_pet_state(pet), now=1800000000)
        episode = pet.moodlets.active[0]
        pet.recognize_food_handover("gift:2", "apple")
        self.assertEqual(pet.moodlets.active[0], episode)
        self.assertEqual(pet.wishes.food_handovers[1].accounted_wish_ids, (1,))
        self.assertIsNone(pet.wishes.food_handovers[1].resolved_wish_instance_id)

    def test_actual_withdrawal_cancels_pending_context_before_recognition(self):
        pet = pet_with(wish(WishId.AVOID_FOOD, "apple"))
        pet.begin_food_handover("gift:1", object_id="object_1")
        pet.withdraw_food_handovers(frozenset(("object_1",)))
        pet = decode_pet_state(encode_pet_state(pet), now=1800000000)
        before = pet.capture_checkpoint()
        pet.recognize_food_handover("gift:1", "apple")
        self.assertEqual(pet.capture_checkpoint(), before)
        self.assertFalse(pet.moodlets.active)

    def test_new_unwanted_handover_stacks_but_repeated_observation_does_not(self):
        pet = pet_with(wish(WishId.AVOID_FOOD, "apple"))
        for instance in range(1, 5):
            goal = wish(WishId.AVOID_FOOD, "apple", instance=instance)
            pet.restore_checkpoint(replace(
                pet.capture_checkpoint(), wishes=replace(
                    pet.wishes, active=(goal,), next_instance_id=instance + 1,
                ),
            ))
            pet.begin_food_handover(f"gift:{instance}", object_id=f"object_{instance}")
            pet.recognize_food_handover(f"gift:{instance}", "apple")
        episode = pet.moodlets.active[0]
        self.assertEqual((episode.level, episode.remaining_seconds), (3, 1800))
        self.assertEqual([c.event_id for c in episode.causes],
                         ["gift:2", "gift:3", "gift:4"])
