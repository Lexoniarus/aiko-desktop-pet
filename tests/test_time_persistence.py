"""Optional elapsed-history migration and exactly-once saved continuation."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.active_time import (
    ActiveSessionClock,
    SessionInputs,
    advance_session_time,
)
from aiko_pet.application.session import LoadedPetData, PetSessionRestorer
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.state import PetState

NOW = datetime(2026, 10, 12, 12).timestamp()


class TimePersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-time-test-")
        self.addCleanup(folder.cleanup)
        self.store = StateStore(Path(folder.name) / "state.json")

    def test_legacy_save_starts_neutral_elapsed_history_without_resetting_needs(
        self,
    ) -> None:
        old = {
            "version": 1,
            "pet": {"updated_at": NOW - 3600, "satiety": 60, "friendship": 45},
            "settings": {"auto_routine": False},
        }
        self.store.path.write_text(json.dumps(old), encoding="utf-8")
        decoded = self.store.load_session(now=NOW).state
        self.assertEqual(decoded.lived_seconds, 0)
        self.assertEqual((decoded.satiety, decoded.friendship), (60, 45))
        restored = PetSessionRestorer(self.store, wall_time=lambda: NOW).restore()
        self.assertEqual(restored.state.lived_seconds, 3600)
        self.assertAlmostEqual(restored.state.satiety, 52)
        self.assertEqual(restored.state.friendship, 45)
        self.assertEqual(restored.state.care_last_rewards, {})

    def test_long_gap_round_trips_then_same_instant_restart_is_unchanged(self) -> None:
        self.store.save(
            PetState(updated_at=NOW, lived_seconds=123.5),
            PetSettings(auto_routine=False),
        )
        end = NOW + 3 * 86400
        session = PetSessionRestorer(self.store, wall_time=lambda: end).restore()
        self.assertEqual(session.state.lived_seconds, 123.5 + 3 * 86400)
        self.assertEqual(session.state.energy, 0)
        self.store.save(session.state, session.settings)
        restarted = PetSessionRestorer(self.store, wall_time=lambda: end).restore()
        self.assertEqual(
            encode_pet_state(restarted.state), encode_pet_state(session.state),
        )
        self.assertEqual(json.loads(self.store.path.read_text())["version"], 1)

    def test_closed_and_standby_paths_agree_on_the_same_unknown_interval(self) -> None:
        pet = PetState(updated_at=NOW, lived_seconds=42)
        self.store.save(pet, PetSettings(auto_routine=False))
        end = NOW + 30 * 3600
        closed = PetSessionRestorer(self.store, wall_time=lambda: end).restore().state
        uptime = [100.0]
        clock = ActiveSessionClock(lambda: uptime[0])
        uptime[0] += 30 * 3600
        advance_session_time(
            pet, clock, SessionInputs(end, 0, False, None, False, False, None),
        )
        self.assertEqual(encode_pet_state(closed), encode_pet_state(pet))

    def test_restore_anchor_includes_initialization_time_without_replay(self) -> None:
        self.store.save(
            PetState(updated_at=NOW - 3600), PetSettings(auto_routine=False),
        )
        uptime = [100.0]
        clock = ActiveSessionClock(lambda: uptime[0], wall_time=lambda: NOW - 5)
        uptime[0] = 105
        original = self.store.load_session

        def slow_load(*, now: float | None = None) -> LoadedPetData:
            result = original(now=now)
            uptime[0] += 60
            return result

        with patch.object(self.store, "load_session", side_effect=slow_load):
            restored = PetSessionRestorer(
                self.store, wall_time=lambda: NOW, clock=clock,
            ).restore()
        self.assertEqual(restored.state.lived_seconds, 3600)
        advance_session_time(
            restored.state, clock,
            SessionInputs(NOW + 60, 0, False, None, False, False, None),
        )
        self.assertEqual(restored.state.lived_seconds, 3660)

    def test_elapsed_axis_survives_checkpoint_restore_and_wall_rebase(self) -> None:
        pet = PetState(updated_at=NOW, lived_seconds=500)
        checkpoint = pet.capture_checkpoint()
        pet.advance(NOW - 86400, elapsed_seconds=60)
        self.assertEqual(pet.lived_seconds, 560)
        pet.anchor_live_session(NOW)
        self.assertEqual(pet.lived_seconds, 560)
        pet.restore_checkpoint(checkpoint)
        self.assertEqual(pet.lived_seconds, 500)
        self.assertEqual(pet.updated_at, NOW)

    def test_malformed_or_future_time_is_backed_up_without_losing_pet_progress(
        self,
    ) -> None:
        for raw in (None, [], {"version": 99, "lived_seconds": 123},
                    {"version": 1, "lived_seconds": -1},
                    {"version": 1, "lived_seconds": True},
                    {"version": 1, "lived_seconds": "bad"}):
            with self.subTest(raw=raw):
                payload = {
                    "version": 1,
                    "pet": {"updated_at": NOW, "satiety": 42, "time": raw},
                }
                original = json.dumps(payload).encode()
                self.store.path.write_bytes(original)
                loaded = self.store.load_session(now=NOW)
                self.assertEqual(loaded.state.satiety, 42)
                self.assertEqual(loaded.state.lived_seconds, 0)
                self.store.save(loaded.state, loaded.settings)
                backups = self.store.path.parent.glob("*.aiko-save-backup")
                self.assertIn(original, [path.read_bytes() for path in backups])

    def test_nonfinite_and_unrepresentable_saved_time_is_neutral(self) -> None:
        for raw in (float("inf"), float("nan"), 10**1000):
            with self.subTest(raw=raw):
                pet = decode_pet_state({
                    "satiety": 42,
                    "updated_at": raw,
                    "time": {"version": 1, "lived_seconds": raw},
                }, now=NOW)
                self.assertEqual(pet.lived_seconds, 0)
                self.assertEqual(pet.updated_at, NOW)
                self.assertEqual(pet.satiety, 42)

    def test_replacing_future_time_without_loading_preserves_original(self) -> None:
        original = json.dumps({
            "version": 1,
            "pet": {"time": {"version": 99, "future": "preserve"}},
        }).encode()
        self.store.path.write_bytes(original)
        self.store.save(PetState(updated_at=NOW), PetSettings())
        backups = self.store.path.parent.glob("*.aiko-save-backup")
        self.assertEqual([path.read_bytes() for path in backups], [original])


if __name__ == "__main__":
    unittest.main()
