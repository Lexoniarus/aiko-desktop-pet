"""Presentation status contracts remain immutable and detached from state."""

import unittest
from dataclasses import FrozenInstanceError

from aiko_pet.presentation.contracts import (
    StatusSnapshot,
)


class ReadContractTests(unittest.TestCase):
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
