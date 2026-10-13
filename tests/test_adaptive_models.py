"""Saved adaptive profiles decode safely without keeping raw history."""

import unittest

from aiko_pet.personality.adaptive_models import (
    SLOTS,
    AdaptiveMemory,
)


class AdaptiveModelBoundaryTests(unittest.TestCase):
    def test_corrupt_saved_profile_does_not_create_raw_history(self) -> None:
        restored = AdaptiveMemory.from_dict({
            "hour_seconds": [2, 3],
            "strain": "garbage",
            "last_contact_wall": 1_800_000_000,
        })
        self.assertEqual(len(restored.hour_seconds), SLOTS)
        self.assertEqual(sum(restored.hour_seconds), 0)
        self.assertEqual(restored.strain, 0)
        self.assertEqual(restored.last_contact_wall, 1_800_000_000)
        self.assertEqual(
            AdaptiveMemory.from_dict(restored.to_dict()).to_dict(),
            restored.to_dict(),
        )


if __name__ == "__main__":
    unittest.main()
