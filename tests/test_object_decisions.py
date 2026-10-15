"""Curiosity is independent from canonical capacity and need-based use."""

import unittest
from dataclasses import replace

from aiko_pet.pet.consumption import ConsumptionOrigin
from aiko_pet.pet.mind.object_decisions import decide_object_use
from aiko_pet.pet.mind.object_knowledge import ObjectKnowledge
from aiko_pet.pet.state import PetState


class ObjectDecisionTests(unittest.TestCase):
    def test_satiated_ground_food_is_deferred_but_handover_uses_existing_capacity(self):
        known = ObjectKnowledge("one", "onigiri", "food", 0, 0, True, 0)
        state = PetState(satiety=76)
        self.assertFalse(decide_object_use(known, state).consume)
        self.assertTrue(decide_object_use(
            known, state, ConsumptionOrigin.HANDOVER,
        ).consume)
        state.satiety = 96
        self.assertFalse(decide_object_use(
            known, state, ConsumptionOrigin.HANDOVER,
        ).consume)

    def test_drink_boundary_and_unrecognized_object_do_not_invent_need(self):
        known = ObjectKnowledge("one", "energy_drink", "drink", 0, 0, True, 0)
        state = PetState(energy=60)
        self.assertTrue(decide_object_use(known, state).consume)
        state.energy = 60.1
        self.assertFalse(decide_object_use(known, state).consume)
        self.assertFalse(decide_object_use(
            replace(known, identity=None), state,
        ).consume)
