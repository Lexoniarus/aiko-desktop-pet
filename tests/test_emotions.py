"""Emotional composition uses every cause independently of care and numeric caps."""

import unittest
from dataclasses import replace

from aiko_pet.infrastructure.moodlet_codec import decode_moodlets, encode_moodlets
from aiko_pet.pet.emotions import EmotionalState, derive_emotional_state
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import (
    MoodletAttribution,
    MoodletEpisode,
    MoodletId,
    MoodletState,
)
from aiko_pet.pet.needs import NeedCondition, NeedLevels, assess_need_conditions

DEFINITIONS = MOODLET_CATALOG.definitions


def episode(key, level=1, instance=1, trigger=0):
    return MoodletEpisode(instance, key, level, 0, trigger, 7200)


def derive(*episodes, mood: float = 60):
    return derive_emotional_state(mood, episodes, definitions=DEFINITIONS)


class EmotionalCompositionTests(unittest.TestCase):
    def test_no_moodlets_use_exact_numeric_boundaries(self):
        for mood, state in (
            (0, EmotionalState.SUBDUED),
            (39.99, EmotionalState.SUBDUED),
            (40, EmotionalState.CALM),
            (69.99, EmotionalState.CALM),
            (70, EmotionalState.SATISFIED),
            (100, EmotionalState.SATISFIED),
        ):
            self.assertEqual(derive(mood=mood).primary, state)

    def test_all_eighteen_families_have_the_documented_direction(self):
        for key, definition in DEFINITIONS.items():
            value = derive(episode(key))
            self.assertEqual(value.primary.value, definition.direction.value)
            self.assertEqual(value.influences[0].cause, key)
        self.assertEqual(len(DEFINITIONS), 18)

    def test_all_active_intensities_participate_without_numeric_caps(self):
        positive = [
            episode(key, min(3, len(d.level_points)), i + 1)
            for i, (key, d) in enumerate(DEFINITIONS.items())
            if d.polarity == "positive"
        ]
        result = derive(*positive)
        self.assertEqual(len(result.influences), 8)
        self.assertEqual(result.positive_intensity, 22)
        self.assertEqual(sum(n for _, n in result.directions), 22)
        self.assertEqual(result.primary, EmotionalState.CHEERFUL)

    def test_equal_positive_negative_preserve_both_as_ambivalent(self):
        value = derive(episode(MoodletId.PRIDE, 2), episode(MoodletId.POKING, 2, 2))
        self.assertEqual(value.primary, EmotionalState.AMBIVALENT)
        self.assertEqual((value.positive_intensity, value.negative_intensity), (2, 2))
        self.assertEqual(len(value.directions), 2)

    def test_four_positive_causes_outweigh_one_level_three_negative(self):
        keys = (
            MoodletId.FOOD_FULFILLED,
            MoodletId.SHARED_PLAY,
            MoodletId.CONNECTION,
            MoodletId.SECURE,
        )
        value = derive(
            *(episode(key, instance=i + 1) for i, key in enumerate(keys)),
            episode(MoodletId.POKING, 3, 5),
            mood=10,
        )
        self.assertEqual(value.primary, EmotionalState.CHEERFUL)
        self.assertEqual(value.negative_intensity, 3)
        self.assertEqual(len(value.influences), 5)

    def test_direction_tie_uses_latest_cause_then_intensity_then_stable_order(self):
        pride = episode(MoodletId.PRIDE, 2, trigger=10)
        cheerful = episode(MoodletId.CHEERFUL, 2, 2, 20)
        self.assertEqual(derive(pride, cheerful).primary, EmotionalState.CHEERFUL)
        self.assertEqual(
            derive(replace(pride, last_trigger_at=20), cheerful).primary,
            EmotionalState.CHEERFUL,
        )
        causes = (
            episode(MoodletId.CONNECTION, 1, 3, 20),
            episode(MoodletId.SECURE, 1, 4, 20),
        )
        self.assertEqual(derive(pride, *causes).primary, EmotionalState.AFFECTIONATE)
        self.assertEqual(
            derive(replace(pride, last_trigger_at=20), *causes).primary,
            EmotionalState.PROUD,
        )

    def test_physical_conditions_coexist_without_becoming_emotional_labels(self):
        self.assertEqual(
            assess_need_conditions(NeedLevels(0, 0, 0, 0, 0)), frozenset(NeedCondition)
        )
        self.assertFalse(assess_need_conditions(NeedLevels(100, 100, 100, 100, 100)))
        self.assertEqual(
            derive(episode(MoodletId.PRIDE), mood=20).primary, EmotionalState.PROUD
        )

    def test_known_cause_attribution_survives_and_old_saves_do_not_invent_it(self):
        stored = MoodletState(
            0,
            2,
            (replace(episode(MoodletId.PRIDE), attribution=MoodletAttribution.USER),),
        )
        raw = encode_moodlets(stored)
        loaded = decode_moodlets(raw, 100)
        self.assertEqual(
            derive(*loaded.active).influences[0].attribution, MoodletAttribution.USER
        )
        del raw["active"][0]["attribution"]
        self.assertEqual(
            decode_moodlets(raw, 100).active[0].attribution, MoodletAttribution.UNKNOWN
        )
        raw["active"][0]["attribution"] = "invented"
        with self.assertRaises(ValueError):
            decode_moodlets(raw, 100)
