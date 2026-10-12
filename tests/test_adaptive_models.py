"""Legacy adaptive model imports remain valid after model separation."""

import unittest

from aiko_pet.adaptive import (
    AdaptiveMemory as LegacyAdaptiveMemory,
    Behaviour as LegacyBehaviour,
    Observation as LegacyObservation,
    clamp as legacy_clamp,
)
from aiko_pet.adaptive_models import (
    SLOTS,
    AdaptiveMemory,
    Behaviour,
    Observation,
    clamp,
)


class AdaptiveModelBoundaryTests(unittest.TestCase):
    def test_old_imports_are_exact_same_models(self) -> None:
        self.assertIs(LegacyAdaptiveMemory, AdaptiveMemory)
        self.assertIs(LegacyObservation, Observation)
        self.assertIs(LegacyBehaviour, Behaviour)
        self.assertIs(legacy_clamp, clamp)

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
