"""Pet view renderers have one implementation while old imports remain safe."""

import unittest

from aiko_pet.ui.pet_view.animated_pet import AnimatedPet
from aiko_pet.ui.animated_pet import AnimatedPet as LegacyPet
from aiko_pet.ui.pet_view.desktop_window import DesktopWindow
from aiko_pet.ui.desktop_window import DesktopWindow as LegacyWindow


class PetRendererOwnershipTests(unittest.TestCase):
    def test_old_imports_are_same_classes(self) -> None:
        self.assertIs(AnimatedPet, LegacyPet)
        self.assertIs(DesktopWindow, LegacyWindow)
