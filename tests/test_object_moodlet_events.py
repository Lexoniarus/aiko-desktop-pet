"""Object emotions require subjective evidence; blame requires attribution."""

import unittest
from dataclasses import replace

from aiko_pet.application.object_awareness import ObjectAwareness
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.interaction_events import ArrangementDisrupted, WithholdingObserved
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import advance_moodlets
from aiko_pet.pet.needs import NeedLevels
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    WorldSurface,
)
from aiko_pet.world.state import WorldState
from tools.pet_test_support import object_test_attention, set_test_pet_values


class ObjectMoodletEventTests(unittest.TestCase):
    def test_observed_relocation_excludes_minor_unknown_and_withholding_moves(self):
        for known, destination, withholding, expected in (
            (True, 600, False, 1), (True, 105, False, 0),
            (False, 600, False, 0), (True, 600, True, 0),
        ):
            with self.subTest(known=known, x=destination, withholding=withholding):
                world = WorldState(WorldSurface(1600, 900), (ObjectDefinition(
                    "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
                ),))
                item = world.place_resting("apple", 100, ObjectFootprint(8, 8))
                awareness, pet = ObjectAwareness(), PetState(satiety=100)

                def observe(stamp):
                    awareness.update(world.snapshot(), pet, now=stamp, x=100,
                                     height=0, width=100, blocked=True,
                                     attention=object_test_attention(
                                         100, width=100, mode="cursor"))

                observe(0)
                observe(.3)
                if known:
                    awareness.memory.update(tuple(replace(
                        seen, identity="apple", kind="food",
                    ) for seen in awareness.observations), now=.3)
                record = awareness.record_for_instance(item.instance_id)
                assert record is not None
                held = world.take_resting(item.instance_id, expected_revision=0)
                self.assertTrue(awareness.follow_taken(
                    item.instance_id, record, now=.4,
                    attention=object_test_attention(100, width=100),
                ))
                if withholding:
                    awareness.exclude_withholding_relocation(record)
                world.return_user_held(held.instance_id, destination,
                                       expected_revision=held.revision)
                observe(.5)
                disruptions = awareness.disruptions
                observe(.8)
                disruptions += awareness.disruptions
                self.assertEqual(len(disruptions), expected)
                for event in disruptions:
                    pet.experience_interaction(event)
                self.assertEqual(pet.friendship, 14.75 if expected else 15)
                observe(1)
                self.assertEqual(awareness.disruptions, ())

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
