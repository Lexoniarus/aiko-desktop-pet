"""Legacy animation asset contracts preserve class identity."""

import unittest

from aiko_pet.pet.animation.character import AnimationClip, CharacterCatalog


class AnimationContractsTest(unittest.TestCase):
    def test_contract_identity(self) -> None:
        self.assertEqual(AnimationClip.__module__, "aiko_pet.pet.animation.character")
        self.assertEqual(CharacterCatalog.__module__, "aiko_pet.pet.animation.character")

