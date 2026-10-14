"""Pet view renderers have one implementation while old imports remain safe."""

import unittest

from aiko_pet.ui.pet_view.animated_pet import AnimatedPet
from aiko_pet.ui.pet_view.desktop_window import DesktopWindow


class PetRendererOwnershipTests(unittest.TestCase):
    def test_old_imports_are_same_classes(self) -> None:
        self.assertEqual(AnimatedPet.__module__, "aiko_pet.ui.pet_view.animated_pet")
        self.assertEqual(DesktopWindow.__module__, "aiko_pet.ui.pet_view.desktop_window")
