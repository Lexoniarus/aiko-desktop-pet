"""Nutrition is shared; social and friendship credit require human handover."""

import unittest
from copy import deepcopy

from aiko_pet.pet.consumption import ConsumptionOrigin
from aiko_pet.pet.state import PetState


class ConsumptionOriginTests(unittest.TestCase):
    def test_autonomous_food_matches_nutrition_without_human_care(self):
        pet = PetState(satiety=50, social=30)
        human = deepcopy(pet)
        pet.consume_item("onigiri", ConsumptionOrigin.AUTONOMOUS, now=1_800_000_000)
        human.consume_item("onigiri", ConsumptionOrigin.HANDOVER, now=1_800_000_000)
        self.assertEqual(pet.food, human.food)
        self.assertEqual(pet.satiety, human.satiety)
        self.assertEqual(pet.social, 30)
        self.assertEqual(human.social, 31)
        self.assertEqual(pet.friendship, 15)
        self.assertGreater(human.friendship, pet.friendship)

    def test_drink_uses_existing_gain_and_sleeping_pet_does_not_accept(self):
        pet = PetState(energy=50)
        pet.consume_item("energy_drink", ConsumptionOrigin.AUTONOMOUS, now=0)
        self.assertEqual(pet.energy, 60)
        sleeping = PetState(energy=pet.energy, sleeping=True)
        self.assertIsNone(
            sleeping.consume_item("apple", ConsumptionOrigin.HANDOVER, now=0)
        )

    def test_recovery_preserves_identity_and_owned_collections(self):
        pet = PetState(satiety=50)
        before = deepcopy(pet)
        pet.consume_item("onigiri", ConsumptionOrigin.HANDOVER, now=1_800_000_000)
        pet.restore_values(before)
        self.assertEqual(pet, before)
