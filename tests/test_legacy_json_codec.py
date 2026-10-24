"""Legacy import validates present data before any forgiving normalization."""

from __future__ import annotations

import copy
import json
import unittest
from dataclasses import replace
from typing import Any

from test_sqlite_adaptive_rows import profile
from test_sqlite_care_evidence import complete_emotional_state
from test_sqlite_food_handovers import handover_state
from test_sqlite_horoscope import admitted_day
from test_sqlite_social_rows import social_history

from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.infrastructure.legacy_json_codec import decode_legacy_session
from aiko_pet.infrastructure.object_memory_codec import encode_object_memory
from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.infrastructure.social_history_codec import encode_social_history
from aiko_pet.infrastructure.world_catalog import build_consumable_definitions
from aiko_pet.infrastructure.world_codec import encode_world
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.pet.mind.object_knowledge import (
    ObjectMemorySnapshot,
    SavedObjectKnowledge,
)
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import ObjectDefinition, ObjectFootprint, WorldSurface
from aiko_pet.world.state import WorldState

WALL = 1_800_000_000.0


def definitions() -> tuple[ObjectDefinition, ...]:
    return build_consumable_definitions(DEFAULT_CATALOG, load_item_catalog())


def legacy_payload() -> dict[str, Any]:
    pet = PetState(updated_at=WALL, lived_seconds=100000,
                   moodlets=complete_emotional_state(), wishes=handover_state())
    stock = WorldState(WorldSurface(800, 600), definitions())
    item = stock.place_resting("apple", 100, ObjectFootprint(8, 8))
    world = stock.snapshot()
    memory = ObjectMemorySnapshot((SavedObjectKnowledge(
        "memory_1", "apple", "food", 100, 0, True, 80, True, None,
        instance_id=item.instance_id,
    ),), 2)
    return {
        "version": 1, "pet": encode_pet_state(pet),
        "settings": PetSettings(scale=2, zodiac_sign="leo").to_dict(),
        "adaptive": profile().to_dict(),
        "social_history": encode_social_history(
            replace(social_history(), horoscope=admitted_day())),
        "world": encode_world(world, recovery_x=0),
        "object_memory": encode_object_memory(
            memory, world_next_id=world.next_instance_id),
    }


class LegacyJsonCodecTests(unittest.TestCase):
    def decode(self, raw: Any) -> Any:
        return decode_legacy_session(json.dumps(raw).encode(), definitions(), now=WALL)

    def test_current_snapshot_retains_original_goals_causes_and_time(self) -> None:
        raw = legacy_payload()
        loaded = self.decode(raw)
        self.assertEqual(encode_pet_state(loaded.state), raw["pet"])
        self.assertEqual(loaded.settings.to_dict(), raw["settings"])
        self.assertEqual(loaded.adaptive_memory.to_dict(), raw["adaptive"])
        self.assertEqual(encode_social_history(loaded.social_history),
                         raw["social_history"])
        self.assertEqual(loaded.state.updated_at, WALL)
        self.assertTrue(loaded.restored_from_save)
        self.assertEqual(loaded.revision.value, 0)

    def test_absent_older_fields_receive_neutral_defaults_without_care_history(
        self,
    ) -> None:
        loaded = self.decode({"version": 1, "pet": {"satiety": 35, "updated_at": WALL},
                              "settings": {"auto_walk": False},
                              "adaptive": {"strain": 10}})
        self.assertEqual(loaded.state.satiety, 35)
        self.assertEqual(loaded.state.lived_seconds, 0)
        self.assertIsNone(loaded.state.friendship_history.baseline)
        self.assertFalse(loaded.settings.auto_walk)
        self.assertEqual(loaded.adaptive_memory.strain, 10)
        self.assertEqual(loaded.state.moodlets.active, ())
        self.assertEqual(loaded.state.wishes.active, ())

    def test_present_invalid_sections_are_never_defaulted(self) -> None:
        for section in ("pet", "settings", "adaptive", "world", "object_memory",
                        "social_history"):
            for invalid in (None, [], False, {"unknown": 1}):
                with self.subTest(section=section, invalid=invalid):
                    raw = legacy_payload()
                    raw[section] = invalid
                    with self.assertRaises((ValueError, TypeError)):
                        self.decode(raw)

    def test_core_values_reject_coercion_clamping_filtering_and_unknown_fields(
        self,
    ) -> None:
        cases = {
            "satiety": [True, "50", -1, 101, None],
            "updated_at": [True, "1800000000", -1, 1e100],
            "sleeping": [1, "false"], "fun": [float("nan")],
            "nap_until": [4_000_000_001], "friendship_gained_today": [101],
            "care_types_today": [["unknown"], ["pet", "pet"]],
            "care_last_rewards": [{"unknown": 1}, {"pet": True}, {"pet": -1}],
            "meals_today": [["unknown"]], "auto_nap_day": [None],
            "food": [None, {"recent_food_ids": ["unknown"]},
                     {"remaining_digest_minutes": 1e50},
                     {"awake_hours_since_last_food": True}],
            "time": [{"version": True, "lived_seconds": 1},
                     {"version": 1, "lived_seconds": -1},
                     {"version": 1, "lived_seconds": 0, "unknown": 1}],
            "unknown": [1],
        }
        for key, values in cases.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    with self.assertRaises((ValueError, TypeError, OverflowError)):
                        self.decode({"version": 1, "pet": {key: value}})

    def test_present_histories_must_pass_their_strict_owner_codecs(self) -> None:
        for key in ("relationship", "sleep_episode", "moodlets", "wishes"):
            with self.subTest(key=key):
                raw = legacy_payload()
                raw["pet"][key]["version"] = 99
                with self.assertRaises(ValueError):
                    self.decode(raw)

    def test_settings_adaptive_and_world_relationships_are_strict(self) -> None:
        valid = legacy_payload()
        for section, key, value in (
            ("settings", "scale", True), ("settings", "auto_walk", 0),
            ("settings", "zodiac_sign", "unknown"), ("settings", "x", 20001),
            ("adaptive", "hour_seconds", [1]), ("adaptive", "strain", 101),
            ("adaptive", "session_seconds", "10"),
            ("adaptive", "quiet_window", {}),
            ("world", "next_instance_id", 0),
        ):
            with self.subTest(section=section, key=key):
                raw = copy.deepcopy(valid)
                raw[section][key] = value
                with self.assertRaises(ValueError):
                    self.decode(raw)
        del valid["world"]
        with self.assertRaises(ValueError):
            self.decode(valid)

    def test_json_syntax_duplicate_keys_nonfinite_and_envelope_are_rejected(
        self,
    ) -> None:
        for contents in (b'{}', b'[]', b'{', b'\xff',
                         b'{"version":1,"version":1,"pet":{}}',
                         b'{"version":1,"pet":{"satiety":1e999}}',
                         b'{"version":1,"pet":{"satiety":NaN}}',
                         b'{"version":true,"pet":{}}',
                         b'{"version":2,"pet":{}}',
                         b'{"version":1,"pet":{},"unknown":1}'):
            with self.subTest(contents=contents):
                with self.assertRaises((ValueError, UnicodeError)):
                    decode_legacy_session(contents, definitions(), now=WALL)

    def test_unrounded_core_numbers_and_zero_reward_anchors_are_not_lost(self) -> None:
        raw = {"version": 1, "pet": {
            "friendship_gained_today": 0.123456789,
            "food": {"awake_hours_since_last_food": 0.123456789},
            "care_last_rewards": {"pet": 0},
        }}
        loaded = self.decode(raw).state
        self.assertEqual(loaded.friendship_gained_today, 0.123456789)
        self.assertEqual(loaded.food.awake_hours_since_last_food, 0.123456789)
        self.assertEqual(loaded.care_last_rewards, {"pet": 0})
