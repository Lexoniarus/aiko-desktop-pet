"""Import and hardware event contracts after ComputerVoice extraction."""

import unittest

from aiko_pet.computer_voice import ComputerVoice
from aiko_pet.dialogue import ComputerVoice as LegacyComputerVoice
from aiko_pet.system_activity import ComputerSnapshot


class ComputerVoiceModuleTests(unittest.TestCase):
    def test_legacy_import_still_refers_to_the_same_class(self) -> None:
        self.assertIs(LegacyComputerVoice, ComputerVoice)
        self.assertEqual(ComputerVoice.__module__, "aiko_pet.computer_voice")

    def test_new_voice_retains_disabled_or_missing_telemetry_behavior(self) -> None:
        voice = ComputerVoice()
        missing = ComputerSnapshot(measured_at=0)
        self.assertIsNone(voice.observe_change(missing, now=1.0))
        self.assertIsNone(voice.maybe_event(missing, now=1.0))
        self.assertIsNone(voice.classify(missing))


if __name__ == "__main__":
    unittest.main()
