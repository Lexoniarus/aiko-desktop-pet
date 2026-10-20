"""Owned emotional values survive save/checkpoint boundaries without simulation."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Any, cast

from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.moodlet_codec import decode_moodlets, encode_moodlets
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletId, MoodletState
from aiko_pet.pet.state import PetState

WALL = 1_800_000_000.0
ELAPSED = 1000.0


def moodlet_state() -> MoodletState:
    return MoodletState(100, 8, (
        MoodletEpisode(1, MoodletId.POKING, 2, 100, 950, 570, (2, 3), 1),
        MoodletEpisode(3, MoodletId.HUNGER_WORN, 1, 200, 200, 2400, (1,),
                       decay_paused=True),
        MoodletEpisode(5, MoodletId.WITHHELD, 3, 300, 900, 1200,
                       decay_paused=True),
        MoodletEpisode(7, MoodletId.PRIDE, 2, 800, 850, 3600),
    ))


class MoodletPersistenceTests(unittest.TestCase):
    def test_round_trip_retains_all_parallel_episodes_and_used_relief(self):
        state = PetState(lived_seconds=ELAPSED, updated_at=WALL,
                         moodlets=moodlet_state())
        encoded = json.loads(json.dumps(encode_pet_state(state), allow_nan=False))
        for later_wall in (WALL, WALL + 86400, WALL - 86400):
            loaded = decode_pet_state(encoded, now=later_wall)
            self.assertEqual(loaded.moodlets, state.moodlets)
            self.assertEqual(loaded.lived_seconds, ELAPSED)
            self.assertEqual(loaded.mood, state.mood)
            self.assertEqual(loaded.friendship, state.friendship)
        self.assertEqual(len(state.moodlets.active), 4)  # No three-Moodlet limit.
        self.assertEqual(decode_moodlets(encoded["moodlets"], ELAPSED),
                         moodlet_state())

    def test_legacy_save_gets_empty_state_at_its_existing_elapsed_baseline(self):
        state = decode_pet_state({
            "satiety": 42, "friendship": 67,
            "time": {"version": 1, "lived_seconds": ELAPSED},
        }, now=WALL)
        self.assertEqual(state.moodlets, MoodletState(baseline=ELAPSED))
        self.assertEqual((state.satiety, state.friendship), (42, 67))
        self.assertEqual(decode_pet_state({}, now=WALL).moodlets, MoodletState())

    def test_immutable_checkpoint_restore_covers_episodes_and_counters(self):
        state = PetState(lived_seconds=ELAPSED, updated_at=WALL,
                         moodlets=moodlet_state())
        checkpoint = state.capture_checkpoint()
        identity = id(state)
        with self.assertRaises(AttributeError):
            cast(Any, state).moodlets = MoodletState()
        with self.assertRaises(FrozenInstanceError):
            cast(Any, state.moodlets.active[0]).relieved_levels = ()
        state.restore_checkpoint(replace(checkpoint, moodlets=MoodletState()))
        self.assertEqual(state.moodlets.active, ())
        state.restore_checkpoint(checkpoint)
        self.assertEqual(id(state), identity)
        self.assertEqual(state.moodlets, moodlet_state())
        self.assertEqual(copy.deepcopy(state).capture_checkpoint(), checkpoint)

    def test_stage_progress_and_paused_recovery_are_not_reset_on_load(self):
        episode = MoodletEpisode(2, MoodletId.HUNGER_WORN, 2, 200, 200, 2400,
                                 (2,), recovery_since=900)
        raw = encode_moodlets(MoodletState(100, 3, (episode,)))
        restored = decode_moodlets(raw, ELAPSED)
        self.assertEqual(restored.active, (episode,))
        raw["active"][0]["relieved_levels"].clear()
        self.assertEqual(restored.active[0].relieved_levels, (2,))

    def test_bad_sections_reject_duplicates_bounds_types_and_invented_history(self):
        original = encode_moodlets(moodlet_state())
        for field, bad in (
            ("version", True), ("version", 999), ("baseline", ELAPSED + 1),
            ("next_instance_id", 7), ("next_instance_id", True),
            ("active", original["active"] * 5),
        ):
            raw = copy.deepcopy(original)
            raw[field] = bad
            with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                decode_moodlets(raw, ELAPSED)
        for field, bad in (
            ("instance_id", 0), ("definition_id", "unknown"), ("level", 4),
            ("level", True), ("started_at", 99), ("last_trigger_at", ELAPSED + 1),
            ("remaining_seconds", float("nan")), ("remaining_seconds", 1201),
            ("remaining_seconds", 10**1000), ("relieved_levels", [2, 2]),
            ("relieved_levels", [True]), ("pending_repetitions", 3),
            ("decay_paused", 1), ("decay_paused", True), ("recovery_since", 900),
            ("stage_typo", 42),
        ):
            raw = copy.deepcopy(original)
            raw["active"][0][field] = bad
            with self.subTest(field=field), self.assertRaises(ValueError):
                decode_moodlets(raw, ELAPSED)
        for duplicate in ("instance", "family"):
            raw = copy.deepcopy(original)
            if duplicate == "instance":
                raw["active"][1]["instance_id"] = 1
            else:
                raw["active"].append({**raw["active"][0], "instance_id": 6})
            with self.subTest(duplicate=duplicate), self.assertRaises(ValueError):
                decode_moodlets(raw, ELAPSED)

    def test_store_uses_one_v1_save_and_preserves_corruption_before_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            store = StateStore(Path(folder) / "state.json")
            pet = PetState(satiety=42, updated_at=WALL, lived_seconds=ELAPSED,
                           moodlets=moodlet_state())
            store.save(pet, PetSettings())
            self.assertEqual(json.loads(store.path.read_text())["version"], 1)
            loaded = store.load_session(now=WALL + 3600)
            self.assertEqual(loaded.state.moodlets, pet.moodlets)
            self.assertEqual(loaded.state.lived_seconds, ELAPSED)
            for bad in (None, {"version": 999}):
                raw = encode_pet_state(pet)
                raw["moodlets"] = bad
                original = json.dumps(dict(version=1, pet=raw)).encode()
                store.path.write_bytes(original)
                loaded = store.load_session(now=WALL)
                self.assertEqual(loaded.state.satiety, 42)
                self.assertEqual(loaded.state.moodlets, MoodletState(ELAPSED))
                store.save(loaded.state, loaded.settings)
                self.assertIn(original, [p.read_bytes() for p in
                                         Path(folder).glob("*.aiko-save-backup")])

    def test_unloaded_invalid_section_is_backed_up_and_missing_section_is_legacy(self):
        with tempfile.TemporaryDirectory() as folder:
            store = StateStore(Path(folder) / "state.json")
            legacy = dict(version=1, pet={"satiety": 42})
            store.path.write_text(json.dumps(legacy), encoding="utf-8")
            loaded = store.load_session(now=WALL)
            store.save(loaded.state, loaded.settings)
            self.assertFalse(tuple(Path(folder).glob("*.aiko-save-backup")))
            corrupt = json.dumps(dict(version=1, pet={"moodlets": []})).encode()
            store.path.write_bytes(corrupt)
            store.save(PetState(updated_at=WALL), PetSettings())
            self.assertEqual([p.read_bytes() for p in
                              Path(folder).glob("*.aiko-save-backup")], [corrupt])
