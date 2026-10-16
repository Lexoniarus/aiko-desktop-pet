"""Needs create stable goals; small changes and absent truth cannot hijack them."""

import unittest
from dataclasses import replace

from aiko_pet.pet.mind.object_decisions import ObjectUseContext
from aiko_pet.pet.mind.object_intentions import ObjectIntentions
from aiko_pet.pet.mind.object_knowledge import ObjectKnowledge
from aiko_pet.pet.state import PetState

APPLE = ObjectKnowledge("one", "apple", "food", 100, 0, True, 0, assessed=True)


class ObjectIntentionTests(unittest.TestCase):
    def test_offer_refusal_does_not_orphan_a_committed_returning_target(self):
        planner = ObjectIntentions()
        pet = PetState(satiety=76)
        held = replace(APPLE, resting=False)
        planner.assess_offer(held, pet)
        pet.satiety = 100
        self.assertFalse(planner.assess_offer(held, pet).consume)
        goal = planner.choose((held,), pet, x=0, now=1, blocked=True,
                              committed=held.token)
        assert goal is not None
        self.assertEqual(goal.token, held.token)
        # The committed coordinator can finish its decline/put-down; ordinary
        # uncommitted wishes are still invalidated by the next choice.
        self.assertIsNone(planner.choose((held,), pet, x=0, now=2, blocked=True))

    def test_offer_wish_survives_observed_drop_but_rechecks_capacity_and_identity(self):
        planner = ObjectIntentions()
        pet = PetState(satiety=76)
        held = replace(APPLE, resting=False)
        self.assertTrue(planner.assess_offer(held, pet).consume)
        other = replace(APPLE, token="other")
        goal = planner.choose((held, other), pet, x=0, now=1, blocked=True,
                              observed=frozenset((held.token,)))
        assert goal is not None
        self.assertEqual(goal.token, held.token)
        goal = planner.choose((APPLE, other), pet, x=0, now=2, changed=True,
                              observed=frozenset((APPLE.token,)))
        assert goal is not None
        self.assertEqual(goal.use_context, ObjectUseContext.CONTINUING_WISH)
        self.assertEqual(goal.purpose, "consume")
        pet.satiety = 100
        self.assertIsNone(planner.choose((APPLE,), pet, x=0, now=3, changed=True))
        pet.satiety = 76
        planner.assess_offer(held, pet)
        self.assertIsNone(planner.choose((replace(APPLE, identity=None),), pet,
                                         x=0, now=4, blocked=True, changed=True))

    def test_commitment_survives_blocking_carry_and_more_attractive_find(self):
        planner = ObjectIntentions()
        pet = PetState(satiety=50)
        planner.choose((APPLE,), pet, x=0, now=0)
        other = replace(APPLE, token="other", x=1)
        carried = replace(APPLE, resting=False, x=400)
        goal = planner.choose(
            (carried, other), pet, x=0, now=1, blocked=True, changed=True,
            committed=APPLE.token, observed=frozenset((other.token,)),
        )
        assert goal is not None
        self.assertEqual((goal.token, goal.x), (APPLE.token, 400))
        planner.complete(APPLE.token, 2)
        goal = planner.choose((other,), pet, x=0, now=2, changed=True)
        assert goal is not None
        self.assertEqual(goal.token, other.token)

    def test_available_finding_replaces_a_stale_goal_and_missing_places_stay_out(self):
        planner = ObjectIntentions()
        pet = PetState(satiety=50)
        planner.choose((APPLE,), pet, x=0, now=0)
        found = replace(APPLE, token="new", x=300, assessed=False)
        goal = planner.choose((APPLE, found), pet, x=0, now=1,
                               observed=frozenset((found.token,)), changed=True)
        assert goal is not None
        self.assertEqual((goal.token, goal.purpose), ("new", "investigate"))
        self.assertIsNone(planner.choose(
            (replace(APPLE, place_status="missing"),), pet, x=0, now=2, changed=True,
        ))

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
        unknown = replace(APPLE, identity=None, kind=None, assessed=False)
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
                        assessed=False, x=150)
        goal = planner.choose((APPLE, drink), pet, x=0, now=2)
        assert goal is not None
        self.assertEqual(goal.token, "drink")
        self.assertEqual(goal.purpose, "investigate")

    def test_satiated_food_is_investigated_once_then_reconsidered_when_hungry(self):
        planner = ObjectIntentions()
        pet = PetState(satiety=76)
        goal = planner.choose((replace(APPLE, assessed=False),), pet, x=0, now=0)
        assert goal is not None
        self.assertEqual(goal.purpose, "investigate")
        planner.cancel(1)
        self.assertIsNone(planner.choose((APPLE,), pet, x=0, now=20))
        pet.satiety = 69
        goal = planner.choose((APPLE,), pet, x=0, now=21)
        assert goal is not None
        self.assertEqual(goal.purpose, "consume")
