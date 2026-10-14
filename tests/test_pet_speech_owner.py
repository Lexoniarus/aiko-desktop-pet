"""The pet speech presenter has one class identity after migration."""

import unittest

from aiko_pet.ui.pet_view.speech_presenter import SpeechPresenter


class PetSpeechOwnerTests(unittest.TestCase):
    def test_compatibility_identity(self) -> None:
        self.assertEqual(
            SpeechPresenter.__module__, "aiko_pet.ui.pet_view.speech_presenter",
        )
