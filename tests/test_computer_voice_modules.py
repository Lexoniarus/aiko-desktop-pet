"""Import and hardware event contracts after WorkloadEventDetector extraction."""

import unittest

from aiko_pet.pet.mind.workload_events import WorkloadEventDetector
from aiko_pet.telemetry import ComputerSnapshot


class ComputerVoiceModuleTests(unittest.TestCase):
    def test_new_voice_retains_disabled_or_missing_telemetry_behavior(self) -> None:
        voice = WorkloadEventDetector()
        missing = ComputerSnapshot(measured_at=0)
        self.assertIsNone(voice.observe_change(missing, now=1.0))
        self.assertIsNone(voice.maybe_event(missing, now=1.0))
        self.assertIsNone(voice.classify(missing))


if __name__ == "__main__":
    unittest.main()
