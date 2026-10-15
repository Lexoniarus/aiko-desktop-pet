"""Needs create stable goals; small changes and absent truth cannot hijack them."""

import unittest
from dataclasses import replace

from aiko_pet.pet.mind.object_intentions import ObjectIntentions
from aiko_pet.pet.mind.object_knowledge import ObjectKnowledge
from aiko_pet.pet.state import PetState

APPLE = ObjectKnowledge("one", "apple", "food", 100, 0, True, 0, examined=True)


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

    def test_unknown_ground_objects_are_investigated_but_carried_ones_not_pursued(self):
        planner = ObjectIntentions()
        pet = PetState(satiety=10)
        unknown = replace(APPLE, identity=None, kind=None, examined=False)
        goal = planner.choose((unknown,), pet, x=0, now=2, changed=True)
        assert goal is not None
        self.assertEqual(goal.purpose, "investigate")
        self.assertIsNone(planner.choose((replace(unknown, resting=False),), pet,
                                         x=0, now=3, changed=True))

    def test_consumption_pause_does_not_delay_another_objects_first_investigation(self):
        planner = ObjectIntentions()
        pet = PetState(satiety=50, energy=66)
        planner.choose((APPLE,), pet, x=0, now=0)
        planner.cancel(1, consumed=True)
        drink = replace(APPLE, token="drink", identity="energy_drink", kind="drink",
                        examined=False, x=150)
        goal = planner.choose((APPLE, drink), pet, x=0, now=2)
        assert goal is not None
        self.assertEqual(goal.token, "drink")
        self.assertEqual(goal.purpose, "investigate")

    def test_satiated_food_is_investigated_once_then_reconsidered_when_hungry(self):
        planner = ObjectIntentions()
        pet = PetState(satiety=76)
        goal = planner.choose((replace(APPLE, examined=False),), pet, x=0, now=0)
        assert goal is not None
        self.assertEqual(goal.purpose, "investigate")
        planner.cancel(1)
        self.assertIsNone(planner.choose((APPLE,), pet, x=0, now=20))
        pet.satiety = 69
        goal = planner.choose((APPLE,), pet, x=0, now=21)
        assert goal is not None
        self.assertEqual(goal.purpose, "consume")
