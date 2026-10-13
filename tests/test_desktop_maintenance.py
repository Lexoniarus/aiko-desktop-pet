"""Taskbar and z-order maintenance use bounded, independent clocks."""

import unittest

from aiko_pet.desktop.maintenance import DesktopMaintenance


class DesktopMaintenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.updates: list[str] = []
        self.track_changed = True
        self.maintenance = DesktopMaintenance(
            check_taskbar=self._check,
            reposition=lambda: self.updates.append("place"),
            maintain_stack=lambda: self.updates.append("stack"),
            started_at=100.0,
        )

    def _check(self) -> bool:
        self.updates.append("check")
        return self.track_changed

    def test_track_checks_only_every_four_seconds(self) -> None:
        self.maintenance.refresh_track(103.9)
        self.assertEqual(self.updates, [])
        self.maintenance.refresh_track(104.0)
        self.assertEqual(self.updates, ["check", "place"])
        self.track_changed = False
        self.maintenance.refresh_track(108.0)
        self.assertEqual(self.updates, ["check", "place", "check"])

    def test_stack_check_keeps_independent_period(self) -> None:
        self.maintenance.refresh_stack(101.49)
        self.assertEqual(self.updates, [])
        self.maintenance.refresh_stack(101.5)
        self.assertEqual(self.updates, ["stack"])
        self.maintenance.refresh_stack(102)
        self.assertEqual(self.updates, ["stack"])
        self.maintenance.refresh_stack(103)
        self.assertEqual(self.updates, ["stack", "stack"])


if __name__ == "__main__":
    unittest.main()
