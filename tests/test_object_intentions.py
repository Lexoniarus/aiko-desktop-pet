"""Needs create stable goals; small changes and absent truth cannot hijack them."""

import unittest
from dataclasses import replace

from aiko_pet.pet.mind.object_intentions import ObjectIntentions
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.pet.state import PetState

APPLE = ObjectObservation("one", "apple", "food", 100, 0, True, 0)


class ObjectIntentionTests(unittest.TestCase):
    def test_hunger_reconsiders_known_food_and_retains_it_over_nearer_food(self):
        planner = ObjectIntentions()
        pet = PetState(satiety=90)
        self.assertIsNone(planner.choose((APPLE,), pet, x=0, now=0))
        pet.satiety = 55
        goal = planner.choose((APPLE,), pet, x=0, now=2)
        assert goal is not None
        nearer = replace(APPLE, token="two", x=10)
        self.assertEqual(planner.choose((nearer, APPLE), pet, x=0, now=3), goal)

    def test_drink_uses_energy_not_food_and_cooldown_prevents_immediate_retry(self):
        drink = replace(APPLE, identity="energy_drink", kind="drink")
        planner = ObjectIntentions()
        pet = PetState(satiety=100, energy=40)
        self.assertIsNotNone(planner.choose((drink,), pet, x=0, now=0))
        planner.cancel(1, consumed=True)
        self.assertIsNone(planner.choose((drink,), pet, x=0, now=20))
        self.assertIsNotNone(planner.choose((drink,), pet, x=0, now=32))

    def test_unknown_or_carried_objects_do_not_become_food_goals(self):
        planner = ObjectIntentions()
        pet = PetState(satiety=10)
        for item in (replace(APPLE, identity=None), replace(APPLE, resting=False)):
            self.assertIsNone(planner.choose((item,), pet, x=0, now=2, changed=True))
