"""Moodlet resource contracts, without active episodes or a desktop fixture."""

from __future__ import annotations

import copy
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any, cast

from aiko_pet.pet.balance import BALANCE, parse_balance
from aiko_pet.pet.catalog_validation import load_json
from aiko_pet.pet.content import GERMAN_TEXT
from aiko_pet.pet.moodlet_catalog import (
    MOODLET_CATALOG,
    load_packaged_moodlet_catalog,
    parse_moodlet_catalog,
)
from aiko_pet.pet.moodlets import (
    EmotionalDirection,
    FoodMonotonyParameters,
    MoodletDecay,
    MoodletId,
    MoodletPolarity,
    PettingParameters,
    PoorCareParameters,
)

DATA = Path(__file__).resolve().parents[1] / "aiko_pet/data"


class MoodletCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = load_json(DATA / "moodlets.json")

    def test_packaged_families_preserve_approved_strengths_and_durations(self):
        catalog = load_packaged_moodlet_catalog()
        self.assertEqual(catalog, MOODLET_CATALOG)
        self.assertEqual(len(catalog.definitions), 18)
        self.assertEqual(sum(d.polarity == MoodletPolarity.POSITIVE
                             for d in catalog.definitions.values()), 8)
        for key, seconds in (
            (MoodletId.POKING, 1200), (MoodletId.CROWDED, 1200),
            (MoodletId.WITHHELD, 1200), (MoodletId.DISRUPTED, 1800),
            (MoodletId.FOOD_MONOTONY, 14400),
        ):
            definition = catalog.definitions[key]
            self.assertEqual(definition.decay_stage_seconds, seconds)
            self.assertEqual(definition.level_points, (-5, -10, -15))
        for definition in catalog.definitions.values():
            if definition.polarity == MoodletPolarity.POSITIVE:
                self.assertEqual(definition.decay_stage_seconds, 7200)
                self.assertEqual(definition.level_points,
                                 (5,) if definition.id == MoodletId.FOOD_FULFILLED
                                 else (5, 10, 15))

    def test_boundaries_and_poor_care_are_typed_separate_parameters(self):
        entries = MOODLET_CATALOG.definitions
        crowded = entries[MoodletId.CROWDED].parameters
        self.assertIsInstance(crowded, PettingParameters)
        assert isinstance(crowded, PettingParameters)
        self.assertEqual(crowded.refusal_seconds, (300, 600, 1200))
        self.assertEqual([(t.maximum_friendship_level, t.affection_threshold)
                          for t in crowded.tolerances], [(2, 60), (5, 80), (10, 90)])
        self.assertEqual((crowded.friendship_loss_points,
                          crowded.friendship_loss_cap_points,
                          crowded.friendship_loss_window_seconds), (.25, 1, 600))
        monotony = entries[MoodletId.FOOD_MONOTONY].parameters
        assert isinstance(monotony, FoodMonotonyParameters)
        self.assertEqual(monotony.free_ignored_portions, 1)
        self.assertEqual(monotony.request_lifetime_seconds, 86400)
        self.assertEqual({d.parameters.need for d in entries.values()
                          if isinstance(d.parameters, PoorCareParameters)},
                         {"satiety", "energy", "fun", "social", "affection"})
        self.assertEqual(entries[MoodletId.HUNGER_WORN].decay,
                         MoodletDecay.STABLE_RECOVERY)
        self.assertEqual(entries[MoodletId.WITHHELD].decay,
                         MoodletDecay.RESOLVED_QUIET_TIME)
        self.assertEqual(entries[MoodletId.EXHAUSTION_IRRITATED].relief_seconds, 0)
        self.assertEqual(entries[MoodletId.FOOD_MONOTONY].relief_seconds, 3600)

    def test_packaged_emotional_directions_cover_the_agreed_composition(self):
        expected = {
            "cheerful": {"food_fulfilled", "shared_play", "cheerful", "enthusiastic"},
            "proud": {"pride"}, "relieved": {"relief"},
            "affectionate": {"connection", "secure"},
            "irritated": {"poking", "food_monotony", "exhaustion_irritated"},
            "crowded": {"crowded"},
            "frustrated": {"withheld", "disrupted", "unstimulated"},
            "downcast": {"hunger_worn"}, "lonely": {"lonely", "missing_closeness"},
        }
        self.assertEqual({direction.value: {
            d.id.value for d in MOODLET_CATALOG.definitions.values()
            if d.direction == direction
        } for direction in EmotionalDirection}, expected)

    def test_catalogue_and_nested_values_are_immutable(self):
        entries = MOODLET_CATALOG.definitions
        with self.assertRaises(TypeError):
            cast(dict[Any, Any], entries)[MoodletId.POKING] = None
        with self.assertRaises(FrozenInstanceError):
            cast(Any, entries[MoodletId.POKING]).relief_seconds = 0
        with self.assertRaises(FrozenInstanceError):
            cast(Any, entries[MoodletId.CROWDED].parameters).refusal_seconds = ()

    def test_schema_rejects_bad_versions_missing_and_duplicate_families(self):
        for version in (True, 1.0, 2):
            with self.subTest(version=version), self.assertRaises(ValueError):
                parse_moodlet_catalog({**self.raw, "version": version})
        for rows in ([], self.raw["moodlets"][:-1],
                     [*self.raw["moodlets"], self.raw["moodlets"][0]]):
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                parse_moodlet_catalog({**self.raw, "moodlets": rows})

    def test_bad_types_signs_units_fields_and_prerequisites_are_rejected(self):
        for key, field, bad in (
            ("poking", "id", "unknown"), ("poking", "direction", []),
            ("poking", "direction", "cheerful"),
            ("poking", "group", "game_wish"),
            ("poking", "level_points", [-5, -10, True]),
            ("poking", "level_points", [-5, 10, -15]),
            ("poking", "level_points", [-5, -5, -15]),
            ("poking", "decay_stage_seconds", 1.5),
            ("poking", "relief_seconds", float("nan")),
            ("poking", "decay_stage_seconds", 0),
            ("withheld", "decay", "quiet_time"),
            ("poking", "decay_stage_secondz", 1200),
            ("secure", "relief_seconds", 300),
            ("secure", "parameters", {}),
        ):
            raw = copy.deepcopy(self.raw)
            row = next(r for r in raw["moodlets"] if r["id"] == key)
            row[field] = bad
            with self.subTest(key=key, field=field, bad=bad):
                with self.assertRaises(ValueError):
                    parse_moodlet_catalog(raw)

    def test_trigger_parameters_validate_tolerance_budgets_and_source_need(self):
        for key, field, bad in (
            ("poking", "escalation_pokes", True),
            ("crowded", "tolerances", []),
            ("crowded", "tolerances", [
                {"maximum_friendship_level": 9, "affection_threshold": 90},
            ]),
            ("crowded", "refusal_seconds", [300, 200, 1200]),
            ("crowded", "friendship_loss_cap_points", .1),
            ("food_monotony", "sequence_window_seconds", float("inf")),
            ("hunger_worn", "need", "energy"),
            ("withheld", "escalation_seconds", -1),
            ("disrupted", "friendship_loss_window_seconds", 0),
        ):
            raw = copy.deepcopy(self.raw)
            row = next(r for r in raw["moodlets"] if r["id"] == key)
            row["parameters"][field] = bad
            with self.subTest(key=key, field=field), self.assertRaises(ValueError):
                parse_moodlet_catalog(raw)

    def test_missing_localized_description_fails_before_presentation(self):
        keys = set(GERMAN_TEXT.messages) - {"moodlet.poking.description"}
        with self.assertRaisesRegex(ValueError, "poking.*localized"):
            parse_moodlet_catalog(self.raw, text_keys=keys)

    def test_common_balance_owns_caps_and_recovery_without_changing_care(self):
        self.assertEqual(BALANCE.number("moodlets", "positive_cap_points"), 20)
        self.assertEqual(BALANCE.number("moodlets", "negative_cap_points"), 30)
        self.assertEqual(BALANCE.number("moodlets", "recovery_stable_seconds"), 1800)
        original = load_json(DATA / "balance.json")
        for key, bad in (
            ("game_wish_cap_points", 21), ("poor_care_cap_points", 31),
            ("recovery_need_threshold", 20), ("critical_level_two_seconds", 7200),
            ("zero_level_one_seconds", 10000), ("relief_shared_play_rounds", True),
        ):
            raw = copy.deepcopy(original)
            raw["moodlets"][key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                parse_balance(raw)
