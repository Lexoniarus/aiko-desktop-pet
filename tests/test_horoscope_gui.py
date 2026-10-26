"""Real isolated Tk: offline book placement is physical, never an HTTP fetch."""

from __future__ import annotations

import unittest
from typing import cast

import test_social_gui as support
from test_social_coordinator import ManualSocialWorker

from aiko_pet.application.social_content import SocialCategory
from aiko_pet.gui import DesktopPet
from aiko_pet.ui.windows.social_menu import SocialMenu
from aiko_pet.world.contracts import ObjectInteraction, ObjectState


class HoroscopeGuiTests(unittest.TestCase):
    pet: DesktopPet
    worker: ManualSocialWorker

    @classmethod
    def setUpClass(cls) -> None:
        support.SocialGuiTests.setUpClass()

    def setUp(self) -> None:
        support.SocialGuiTests.setUp(cast(support.SocialGuiTests, self))

    def menu(self) -> SocialMenu:
        return support.SocialGuiTests.menu(cast(support.SocialGuiTests, self))

    # Reuse only fixture setup, not the inherited online-service tests.
    def test_local_book_choice_does_not_require_online_opt_in(self):
        self.pet._preferences.set_zodiac("taurus")
        self.assertFalse(self.pet.settings.online_social)
        menu = self.menu()
        menu.refresh()
        self.assertEqual(menu.buttons[SocialCategory.HOROSCOPE].cget("state"), "normal")
        before = self.pet.state.social
        menu.choose(SocialCategory.HOROSCOPE)
        self.assertTrue(self.pet._world.cursor.carrying)
        token = self.pet._world.cursor.instance_id
        assert token is not None
        book = self.pet._world.world.get(token)
        self.assertEqual(book.definition_id, "horoscope_book")
        self.assertEqual(book.state, ObjectState.USER_HELD)
        definition = next(
            d
            for d in self.pet._world.world.snapshot().definitions
            if d.definition_id == "horoscope_book"
        )
        self.assertIn(ObjectInteraction.READ, definition.interactions)
        self.assertEqual(self.pet.state.social, before)
        self.assertFalse(self.worker.requests)

    def test_book_world_size_and_support_match_native_scales(self):
        view = self.pet._world.view
        for scale in (1, 2):
            image = view.image("horoscope_book", scale)
            self.assertEqual((image.width(), image.height()), (128 * scale, 96 * scale))
            self.assertEqual(
                view.ground_pivot("horoscope_book", scale), (64 * scale, 80 * scale)
            )
            sprite = view.sprite("horoscope_book", scale)
            self.assertEqual(sprite.pivot, view.ground_pivot("horoscope_book", scale))

    def test_missing_sign_disables_book(self):
        self.assertFalse(self.pet._care_runtime.horoscope_choice()[1])

    def test_placing_first_book_disables_a_second_before_reading(self):
        self.pet._preferences.set_zodiac("taurus")
        self.pet._world.begin_carry("horoscope_book")
        token = self.pet._world.cursor.instance_id
        assert token is not None
        self.pet._world.cursor.release()
        self.assertFalse(self.pet._care_runtime.horoscope_choice()[1])
        self.pet._world.begin_carry("horoscope_book")
        self.assertFalse(self.pet._world.cursor.carrying)
        self.assertEqual(len(self.pet._world.world.snapshot().objects), 1)
