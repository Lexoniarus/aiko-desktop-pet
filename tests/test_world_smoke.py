"""Smoke profiles are isolated and explicit restart never reseeds state."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.world_smoke import prepare_session


class WorldSmokeTests(unittest.TestCase):
    def test_curious_profile_reproduces_the_reported_need_levels(self):
        with tempfile.TemporaryDirectory() as folder:
            store = prepare_session(Path(folder) / "state.json", scenario="curious")
            session = store.load_session()
            self.assertEqual(session.state.satiety, 76)
            self.assertEqual(session.state.energy, 60)
            self.assertFalse(session.settings.spontaneous_talk)

    def test_hungry_and_full_profiles_have_different_needs_without_random_walk(self):
        with tempfile.TemporaryDirectory() as folder:
            for scenario, level in (("hungry", 55), ("full", 100)):
                store = prepare_session(Path(folder) / scenario / "state.json",
                                        scenario=scenario)
                session = store.load_session()
                self.assertEqual(session.state.satiety, level)
                self.assertFalse(session.settings.auto_walk)
                self.assertFalse(session.settings.auto_routine)
                prepare_session(store.path,
                                scenario="full" if level == 55 else "hungry")
                self.assertEqual(store.load_session().state.satiety, level)

    def test_normal_save_path_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "normal.json"
            with patch("tools.world_smoke.default_save_path", return_value=path):
                with self.assertRaises(ValueError):
                    prepare_session(path, scenario="hungry")
            self.assertFalse(path.exists())
