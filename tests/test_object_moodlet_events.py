"""Object emotions require subjective evidence; blame requires attribution."""

import unittest

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.interaction_events import ArrangementDisrupted, WithholdingObserved
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import advance_moodlets
from aiko_pet.pet.needs import NeedLevels
from aiko_pet.pet.state import PetState
from tools.pet_test_support import set_test_pet_values


class ObjectMoodletEventTests(unittest.TestCase):
    def test_absence_emotion_and_attributed_loss_are_independent_and_persisted(self):
        pet = PetState(friendship=50)
        pet.experience_interaction(ArrangementDisrupted())
        self.assertEqual(pet.friendship, 50)
        for _ in range(5):
            pet.experience_interaction(ArrangementDisrupted(attributed=True))
        self.assertEqual(pet.moodlets.active[0].level, 3)
        self.assertEqual(pet.friendship, 49)
        pet = decode_pet_state(encode_pet_state(pet), now=pet.updated_at)
        pet.experience_interaction(ArrangementDisrupted(attributed=True))
        self.assertEqual(pet.friendship, 49)
        set_test_pet_values(pet, lived_seconds=3600)
        pet.experience_interaction(ArrangementDisrupted(attributed=True))
        self.assertEqual(pet.friendship, 48.75)

    def test_unobserved_time_releases_withholding_and_never_escalates_or_charges(self):
        pet = PetState(friendship=50)
        pet.experience_interaction(WithholdingObserved())
        aged = advance_moodlets(pet.moodlets, 1200, elapsed=0,
                                before=NeedLevels(50, 50, 50, 50, 50),
                                after=NeedLevels(50, 50, 50, 50, 50),
                                definitions=MOODLET_CATALOG.definitions,
                                observed=False)
        self.assertFalse(aged.active)
        self.assertEqual(pet.friendship, 50)
