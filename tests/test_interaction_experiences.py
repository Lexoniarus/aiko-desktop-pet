"""Actual incident causes, without reclassifying fair outcomes as mistreatment."""

import unittest
from dataclasses import replace

from test_wish_assignment import wish

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.interaction_events import (
    BoundaryCommunicated,
    Poked,
    WithholdingEnded,
    WithholdingObserved,
)
from aiko_pet.pet.moodlets import MoodletCauseKind, MoodletId
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import WishId, WishState
from aiko_pet.ui.view_models.moodlet_causes import cause_description
from tools.pet_test_support import require_test_value

WALL = 1800000000


class InteractionExperienceTests(unittest.TestCase):
    def test_one_continuous_poking_incident_retains_concrete_escalation_causes(self):
        pet = PetState(updated_at=WALL)
        pet.experience_interaction(Poked(False))
        self.assertIsNone(pet.moodlets.care_evidence)
        pet.experience_interaction(BoundaryCommunicated("poking"))
        for _ in range(8):
            pet.experience_interaction(Poked(True))
        episode = next(
            e for e in pet.moodlets.active if e.definition_id == MoodletId.POKING
        )
        self.assertGreater(episode.level, 1)
        self.assertEqual(len(episode.causes), episode.level)
        self.assertTrue(
            all(c.kind == MoodletCauseKind.INTERACTION for c in episode.causes)
        )
        self.assertIn("Genervt vom Stupsen", cause_description(episode.causes[0]))
        self.assertEqual(
            len(require_test_value(pet.moodlets.care_evidence).experiences), 1
        )
        saved = decode_pet_state(encode_pet_state(pet), now=WALL)
        self.assertEqual(saved.moodlets, pet.moodlets)

    def test_withholding_escalations_are_one_incident_but_new_attempt_is_another(self):
        pet = PetState(updated_at=WALL)
        for _ in range(3):
            pet.experience_interaction(WithholdingObserved(incident_id="one"))
        self.assertEqual(
            len(require_test_value(pet.moodlets.care_evidence).experiences), 1
        )
        pet.experience_interaction(WithholdingEnded())
        pet._change(lived_seconds=20000)
        pet.experience_interaction(WithholdingObserved(incident_id="two"))
        self.assertEqual(
            len(require_test_value(pet.moodlets.care_evidence).experiences), 2
        )

    def test_unidentified_gift_is_neutral_then_actual_excluded_food_is_upsetting(self):
        for expressed in (None, 0):
            with self.subTest(expressed=expressed):
                desired = replace(
                    wish(WishId.AVOID_FOOD, "apple"), expressed_at=expressed
                )
                pet = PetState(
                    updated_at=WALL, lived_seconds=100, wishes=WishState(2, (desired,))
                )
                pet.begin_food_handover("gift", object_id="actual-apple")
                self.assertIsNone(pet.moodlets.care_evidence)
                pet.recognize_food_handover("gift", "apple")
                event = require_test_value(pet.moodlets.care_evidence).experiences[0]
                self.assertTrue(event.upsetting)
                self.assertFalse(event.pleasant)
                self.assertEqual(event.boundary_violated, expressed is not None)
                self.assertIsNone(event.wish_instance_id)  # Not a fulfillment.
                pet.recognize_food_handover("gift", "apple")
                self.assertEqual(
                    len(require_test_value(pet.moodlets.care_evidence).experiences), 1
                )

    def test_positive_food_handover_and_later_intake_do_not_count_two_visits(self):
        desired = wish(WishId.FOOD, "apple")
        pet = PetState(
            updated_at=WALL,
            lived_seconds=100,
            satiety=30,
            wishes=WishState(2, (desired,)),
        )
        pet.begin_food_handover("gift", object_id="actual-apple")
        pet.recognize_food_handover("gift", "apple")
        from aiko_pet.pet.consumption import ConsumptionOrigin

        pet.consume_item(
            "apple",
            now=WALL,
            origin=ConsumptionOrigin.HANDOVER,
            object_id="actual-apple",
        )
        self.assertEqual(
            len(require_test_value(pet.moodlets.care_evidence).experiences), 1
        )
        self.assertEqual(
            len(require_test_value(pet.moodlets.care_evidence).encounters), 1
        )


if __name__ == "__main__":
    unittest.main()
