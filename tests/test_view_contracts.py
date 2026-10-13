"""Presentation contracts retain identity across old application imports."""

import unittest
from dataclasses import FrozenInstanceError

from aiko_pet.application.view_models import (
    HoverAnchor, HoverSnapshot, SettingsSnapshot, StatusSnapshot,
)
from aiko_pet.ui.hover_contracts import (
    HoverAnchor as LegacyHoverAnchor,
    HoverSnapshot as LegacyHoverSnapshot,
)
from aiko_pet.ui.settings_contracts import SettingsSnapshot as LegacySettings
from aiko_pet.ui.status_contracts import StatusSnapshot as LegacyStatus


class ReadContractTests(unittest.TestCase):
    def test_legacy_reexports_preserve_class_identity(self) -> None:
        self.assertIs(HoverAnchor, LegacyHoverAnchor)
        self.assertIs(HoverSnapshot, LegacyHoverSnapshot)
        self.assertIs(StatusSnapshot, LegacyStatus)
        self.assertIs(SettingsSnapshot, LegacySettings)

    def test_status_data_is_immutable_and_not_a_pet_state(self) -> None:
        status = StatusSnapshot(
            today="Montag", next_event="", hint="", emotion="",
            sleep_label="", hardware_line="", activity_line="",
            needs=(("energy", 72),), friendship_level=2,
        )
        self.assertEqual(status.need_value("energy"), 72)
        with self.assertRaises(FrozenInstanceError):
            setattr(status, "friendship_level", 10)
        with self.assertRaises(KeyError):
            status.need_value("unknown")


if __name__ == "__main__":
    unittest.main()
