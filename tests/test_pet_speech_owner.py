"""The pet speech presenter has one class identity after migration."""

import unittest

from aiko_pet.ui.pet_view.speech_presenter import SpeechPresenter
from aiko_pet.ui.speech_presenter import SpeechPresenter as LegacySpeech


class PetSpeechOwnerTests(unittest.TestCase):
    def test_compatibility_identity(self) -> None:
        self.assertIs(SpeechPresenter, LegacySpeech)
