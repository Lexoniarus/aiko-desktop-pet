"""Application startup and save-decoding contracts without a desktop GUI."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from aiko_pet.personality.adaptive_models import AdaptiveMemory
from aiko_pet.application.session import PetSessionRestorer
from aiko_pet.application.settings import PetSettings
from aiko_pet.pet.state import PetState
from aiko_pet.infrastructure.persistence import StateStore

# Choose a fixed local afternoon; DST and CI host timezone must not matter.
NOW = datetime(2026, 10, 12, 15).astimezone().timestamp()


class SessionRestorationTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.store = StateStore(Path(folder.name) / "state.json")

    def restore(self) -> tuple[PetState, PetSettings, AdaptiveMemory]:
        session = PetSessionRestorer(
            self.store, wall_time=lambda: NOW,
        ).restore()
        return session.state, session.settings, session.adaptive.memory

    def test_missing_save_preserves_original_fresh_start(self) -> None:
        with patch.object(PetState, "advance", autospec=True) as advance:
            state, settings, memory = self.restore()
        advance.assert_not_called()
        self.assertEqual(state.updated_at, NOW)
        self.assertEqual(state.meals_date, "")
        self.assertFalse(state.sleeping)
        self.assertEqual(state.satiety, 75)
        self.assertTrue(settings.auto_routine)
        self.assertEqual(sum(memory.hour_seconds), 0)

    def test_corrupt_or_unsupported_save_does_not_simulate_time(self) -> None:
        for invalid in ("{broken json", '{"version": 999}', "[]"):
            with self.subTest(invalid=invalid):
                self.store.path.write_text(invalid, encoding="utf-8")
                with patch.object(PetState, "advance", autospec=True) as advance:
                    state, _settings, _memory = self.restore()
                advance.assert_not_called()
                self.assertEqual(state.updated_at, NOW)
                self.assertEqual(state.meals_date, "")

    def test_store_load_is_data_only_even_after_long_inactivity(self) -> None:
        saved = PetState(satiety=60, energy=35, updated_at=NOW - 3600)
        settings = PetSettings(auto_routine=False)
        self.store.save(saved, settings)
        with patch.object(PetState, "advance", autospec=True) as advance:
            decoded, restored_settings = self.store.load(now=NOW)
        advance.assert_not_called()
        self.assertEqual(decoded.to_dict(), saved.to_dict())
        self.assertEqual(restored_settings.to_dict(), settings.to_dict())
        self.assertTrue(self.store.load_session(now=NOW).restored_from_save)

    def test_existing_save_freezes_closed_time_and_resets_anchor(self) -> None:
        saved = PetState(satiety=75, updated_at=NOW - 3600)
        self.store.save(saved, PetSettings(auto_routine=False))
        with patch.object(PetState, "advance", autospec=True) as advance:
            state, settings, _memory = self.restore()
        advance.assert_not_called()
        self.assertEqual(state.satiety, 75)
        self.assertEqual(state.updated_at, NOW)

    def test_saved_elapsed_time_and_adaptive_memory_are_preserved(self) -> None:
        saved = PetState(satiety=65, energy=40, updated_at=NOW - 3600)
        settings = PetSettings(
            x=380, scale=2, toolbar_x=30, toolbar_y=40,
            auto_routine=False, learn_rhythm=False,
        )
        memory = AdaptiveMemory()
        memory.hour_seconds[42] = 32.5
        self.store.save(saved, settings, adaptive=memory)
        with patch.object(
            self.store, "_read_payload", wraps=self.store._read_payload,
        ) as reader:
            actual, restored_settings, adaptive_memory = self.restore()
        reader.assert_called_once()
        expected = PetState.from_dict(saved.to_dict(), now=NOW)
        expected.updated_at = NOW
        self.assertEqual(actual.to_dict(), expected.to_dict())
        self.assertEqual(restored_settings.to_dict(), settings.to_dict())
        self.assertEqual(adaptive_memory.hour_seconds[42], 32.5)
        self.assertEqual(self.store.load(now=NOW)[0].updated_at, NOW - 3600)

    def test_saved_auto_routine_setting_does_not_create_offline_recovery(self) -> None:
        saved = PetState(energy=30, updated_at=NOW - 1800)
        settings = PetSettings(auto_routine=True)
        self.store.save(saved, settings)
        with patch.object(PetState, "advance", autospec=True) as advance:
            state, restored_settings, _memory = self.restore()
        advance.assert_not_called()
        self.assertEqual(state.energy, 30)
        self.assertTrue(restored_settings.auto_routine)

    def test_old_version_one_save_without_adaptive_data_still_loads(self) -> None:
        legacy = {
            "version": 1,
            "pet": {"satiety": 42, "updated_at": NOW},
            "settings": {"x": 240, "scale": 2},
        }
        self.store.path.write_text(
            json.dumps(legacy), encoding="utf-8",
        )
        state, settings, memory = self.restore()
        self.assertEqual(state.satiety, 42)
        self.assertEqual((settings.x, settings.scale), (240, 2))
        self.assertEqual(sum(memory.hour_seconds), 0)


if __name__ == "__main__":
    unittest.main()
