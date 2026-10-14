"""Legacy animation asset contracts preserve class identity."""

import unittest

from aiko_pet.pet.animation.character import AnimationClip, CharacterCatalog
from aiko_pet.presentation.character import AnimationClip as LegacyAnimationClip
from aiko_pet.presentation.character import CharacterCatalog as LegacyCharacterCatalog


class AnimationContractsTest(unittest.TestCase):
    def test_contract_identity(self) -> None:
        self.assertIs(AnimationClip, LegacyAnimationClip)
        self.assertIs(CharacterCatalog, LegacyCharacterCatalog)

