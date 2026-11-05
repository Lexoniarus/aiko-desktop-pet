"""Longer-term authored rules remain values, not evidence or running evaluators."""

import copy
import unittest
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from typing import Any, cast

from aiko_pet.pet.catalog_validation import load_json
from aiko_pet.pet.content import GERMAN_TEXT
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG, parse_moodlet_catalog
from aiko_pet.pet.moodlet_patterns import (
    AppreciationParameters,
    GuardedParameters,
    LongTermMoodletPolicy,
    OptimismParameters,
    OverlookedParameters,
    TrustParameters,
    UncertaintyParameters,
)
from aiko_pet.pet.moodlets import MoodletDecay, MoodletGroup, MoodletId

DATA = Path(__file__).resolve().parents[1] / "aiko_pet/data/moodlets.json"


class MoodletPatternCatalogTests(unittest.TestCase):
    def test_six_families_preserve_distinct_qualification_and_decay(self):
        for key, parameters, hours, points in (
            (MoodletId.TRUSTING, TrustParameters(3, 7200, 28800, 2, 1, 0),
             36, (5, 10, 15)),
            (MoodletId.APPRECIATED, AppreciationParameters(3, 2, 2, 7200, 0),
             30, (5, 10, 15)),
            (MoodletId.OPTIMISTIC, OptimismParameters(3, 2, 2, 7200, 1, 1),
             30, (5, 10, 15)),
            (MoodletId.UNCERTAIN, UncertaintyParameters(2, 7200),
             30, (-5, -10, -15)),
            (MoodletId.OVERLOOKED, OverlookedParameters(1, 28800),
             30, (-5, -10, -15)),
            (MoodletId.GUARDED, GuardedParameters(3, 14400),
             36, (-5, -10, -15)),
        ):
            with self.subTest(key=key):
                definition = MOODLET_CATALOG.definitions[key]
                self.assertEqual(definition.parameters, parameters)
                self.assertEqual(definition.group, MoodletGroup.LONG_TERM)
                self.assertEqual(definition.level_points, points)
                self.assertEqual(definition.decay, MoodletDecay.QUIET_TIME)
                self.assertEqual(definition.decay_stage_seconds, hours * 3600)
                self.assertEqual(definition.relief_seconds, 0)
                with self.assertRaises(FrozenInstanceError):
                    setattr(cast(Any, definition.parameters),
                            fields(parameters)[0].name, 0)
        policy = MOODLET_CATALOG.long_term_policy
        self.assertEqual(policy, LongTermMoodletPolicy(86400, 5, 10, .00005, .0001))
        with self.assertRaises(FrozenInstanceError):
            cast(Any, policy).period_seconds = 1

    def test_food_setback_is_distinct_and_does_not_claim_intake_or_direct_loss(self):
        definition = MOODLET_CATALOG.definitions[MoodletId.FOOD_WISH_DISREGARDED]
        self.assertEqual(definition.group, MoodletGroup.FOOD_SETBACK)
        self.assertEqual(definition.level_points, (-5, -10, -15))
        self.assertEqual(definition.decay_stage_seconds, 1800)
        self.assertEqual(definition.decay, MoodletDecay.QUIET_TIME)
        self.assertEqual(definition.relief_seconds, 0)
        self.assertIsNone(definition.parameters)
        self.assertEqual(GERMAN_TEXT.format(definition.label_key),
                         "Essenswunsch missachtet")

    def test_impossible_patterns_and_repurposed_fields_fail_at_load(self):
        for key, field, bad in (
            ("trusting", "minimum_encounters", True),
            ("trusting", "minimum_encounter_gap_seconds", 86400),
            ("trusting", "minimum_encounter_span_seconds", 100),
            ("trusting", "care_exposure_level_limit", 2),
            ("trusting", "maximum_boundary_violations", 1),
            ("appreciated", "minimum_wish_areas", 4),
            ("optimistic", "maximum_kind_per_encounter", 2),
            ("uncertain", "minimum_pairs", 1),
            ("uncertain", "minimum_incident_gap_seconds", float("nan")),
            ("overlooked", "maximum_encounters", 2),
            ("overlooked", "awake_contact_gap_seconds", 86401),
            ("guarded", "minimum_incidents", 2),
            ("guarded", "minimum_incident_span_seconds", 0),
            ("guarded", "friendship_loss_points", 1),
        ):
            raw = load_json(DATA)
            row = next(r for r in raw["moodlets"] if r["id"] == key)
            row["parameters"][field] = bad
            with self.subTest(key=key, field=field), self.assertRaises(ValueError):
                parse_moodlet_catalog(raw)
        for key, field, bad in (
            ("trusting", "group", "game_wish"),
            ("trusting", "parameters", None),
            ("trusting", "direction", "proud"),
            ("guarded", "relief_seconds", 300),
            ("food_wish_disregarded", "group", "interaction"),
            ("food_wish_disregarded", "direction", "irritated"),
        ):
            raw = load_json(DATA)
            row = next(r for r in raw["moodlets"] if r["id"] == key)
            row[field] = bad
            with self.subTest(key=key, field=field), self.assertRaises(ValueError):
                parse_moodlet_catalog(raw)

    def test_shared_policy_rejects_unbounded_or_conflicting_metadata(self):
        original = load_json(DATA)
        for field, bad in (
            ("period_seconds", 3600), ("positive_mood_cap_points", 21),
            ("negative_mood_cap_points", -10), ("positive_friendship_rate", .0031),
            ("negative_friendship_rate", float("inf")),
            ("positive_friendship_rate", True), ("negative_friendship_rate", 0),
            ("observed_incidents", []),
        ):
            raw = copy.deepcopy(original)
            raw["long_term_policy"][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                parse_moodlet_catalog(raw)
        for key in (MoodletId.FOOD_WISH_DISREGARDED, MoodletId.GUARDED):
            keys = set(GERMAN_TEXT.messages) - {f"moodlet.{key}.description"}
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "localized"):
                parse_moodlet_catalog(original, text_keys=keys)
