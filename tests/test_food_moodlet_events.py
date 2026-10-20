"""Actual intake, communicated requests and independent rolling loss budgets."""

import unittest

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.consumption import ConsumptionOrigin
from aiko_pet.pet.interaction_events import FoodConsumed
from aiko_pet.pet.moodlets import MoodletId
from aiko_pet.pet.state import PetState
from tools.pet_test_support import set_test_pet_values


class FoodMoodletEventTests(unittest.TestCase):
    def intake(self, pet, food="apple", *, personal=False, at=None):
        if at is not None:
            set_test_pet_values(pet, lived_seconds=at)
        pet.experience_interaction(FoodConsumed(food, personal))

    def test_only_actual_accepted_intake_creates_a_moodlet(self):
        pet = PetState(satiety=100)
        pet.consume_item("apple", ConsumptionOrigin.HANDOVER, now=pet.updated_at)
        self.assertFalse(pet.moodlets.interactions.food.intakes)
        for _ in range(3):
            set_test_pet_values(pet, satiety=10)
            pet.consume_item("apple", ConsumptionOrigin.AUTONOMOUS, now=pet.updated_at)
        self.assertEqual(pet.moodlets.active[0].definition_id, MoodletId.FOOD_MONOTONY)
        self.assertTrue(pet.moodlets.interactions.food.request_pending)
        self.assertEqual(pet.friendship, 15)

    def test_window_variety_drink_and_bounded_intake_evidence(self):
        pet = PetState()
        self.intake(pet, at=0)
        self.intake(pet, at=1)
        self.intake(pet, at=86401)
        self.assertFalse(pet.moodlets.active)
        self.intake(pet, "energy_drink")
        self.assertEqual(len(pet.moodlets.interactions.food.intakes), 2)
        self.intake(pet, at=86401)
        self.assertTrue(pet.moodlets.active)
        self.intake(pet, "onigiri")
        self.assertEqual(pet.moodlets.active[0].remaining_seconds, 10800)
        self.assertEqual(pet.moodlets.interactions.food.intakes, (86401,))
        self.assertFalse(pet.moodlets.interactions.food.request_pending)
        for _ in range(30):
            self.intake(pet, "onigiri")
        self.assertEqual(pet.moodlets.active[0].level, 3)
        self.assertEqual(len(pet.moodlets.interactions.food.intakes), 3)

    def test_request_delivery_first_reminder_and_persisted_daily_cap(self):
        pet = PetState(friendship=50)
        for _ in range(4):
            self.intake(pet, personal=True)
        self.assertEqual(pet.friendship, 50)
        pet.note_interaction_text("feed_variety_request")
        self.intake(pet, personal=True)
        self.assertEqual(pet.friendship, 50)
        self.intake(pet)  # Autonomous food cannot disregard a personal request.
        self.intake(pet, personal=True)
        self.assertEqual(pet.friendship, 49.75)
        pet = decode_pet_state(encode_pet_state(pet), now=pet.updated_at)
        for _ in range(20):
            self.intake(pet, personal=True)
        self.assertEqual(pet.friendship, 49)
        self.intake(pet, "onigiri", personal=True)
        for _ in range(3):
            self.intake(pet, personal=True)
        pet.note_interaction_text("feed_variety_request")
        self.intake(pet, personal=True)
        self.intake(pet, personal=True)
        self.assertEqual(pet.friendship, 49)  # New request cannot refund the cap.

    def test_request_expiry_does_not_charge_or_refresh_on_displayed_reminder(self):
        pet = PetState(friendship=50)
        for _ in range(3):
            self.intake(pet)
        pet.note_interaction_text("feed_variety_request")
        self.intake(pet, personal=True, at=86400)
        self.assertEqual(pet.friendship, 50)
        pet.note_interaction_text("feed_variety_reminder")
        self.assertEqual(pet.moodlets.interactions.food.requested_at, 0)

    def test_extended_evidence_survives_rollback_and_malformed_food_is_rejected(self):
        pet = PetState()
        before = pet.capture_checkpoint()
        for _ in range(3):
            self.intake(pet)
        saved = encode_pet_state(pet)
        self.assertEqual(decode_pet_state(saved).moodlets, pet.moodlets)
        pet.restore_checkpoint(before)
        self.assertFalse(pet.moodlets.interactions.food.intakes)
        saved["moodlets"]["interactions"]["food"]["intakes"] = [0] * 4
        self.assertFalse(decode_pet_state(saved).moodlets.active)
