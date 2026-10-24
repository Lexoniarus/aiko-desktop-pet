"""Native Tk acceptance with the shared isolated-save fixture and no HTTP."""

from __future__ import annotations

import time
import unittest
from typing import Any, cast
from unittest.mock import patch

import test_social_gui as social_gui_support
from test_horoscope import horoscope_payload, reading
from test_social_coordinator import ManualSocialWorker

from aiko_pet.application.horoscope import prepare_horoscope
from aiko_pet.application.horoscope_models import HoroscopeRequest
from aiko_pet.application.social_content import SocialCategory
from aiko_pet.application.social_coordinator import SocialFetchResult
from aiko_pet.gui import DesktopPet
from aiko_pet.pet.content import GERMAN_TEXT
from tools.desktop_test_support import create_test_desktop


class HoroscopeGuiTests(unittest.TestCase):
    pet: DesktopPet
    worker: ManualSocialWorker

    @classmethod
    def setUpClass(cls):
        social_gui_support.SocialGuiTests.setUpClass()

    def setUp(self):
        social_gui_support.SocialGuiTests.setUp(
            cast(social_gui_support.SocialGuiTests, self)
        )

    def menu(self):
        return social_gui_support.SocialGuiTests.menu(
            cast(social_gui_support.SocialGuiTests, self)
        )

    def begin(self):
        self.pet._preferences.set_zodiac("aries")
        self.pet._preferences.set_option("online_social", True)
        self.menu().choose(SocialCategory.HOROSCOPE)
        self.pet.root.update()
        self.worker.complete(123)
        self.pet._social_runtime.poll()
        category, request = self.worker.requests[-1]
        self.assertEqual(category, SocialCategory.HOROSCOPE)
        assert isinstance(request, HoroscopeRequest)
        item = prepare_horoscope(horoscope_payload(request.sign, request.date), request)
        self.worker.result = SocialFetchResult(request, category, item)
        self.pet._social_runtime.poll()
        self.pet.root.update()
        return item

    def test_sign_option_does_not_fetch_and_missing_sign_disables_choice(self):
        self.pet._hover.open_settings(100, 100)
        settings = self.pet._hover.settings_window
        assert settings is not None
        self.assertEqual(settings.zodiac_value.get(), "Nicht ausgewählt")
        self.assertEqual(len(settings.zodiac_choice.cget("values")), 13)
        settings.zodiac_value.set("Löwe")
        settings._choose_zodiac(cast(Any, None))
        self.assertEqual(self.pet.settings.zodiac_sign, "leo")
        self.assertFalse(self.worker.requests)
        self.pet._preferences.set_zodiac(None)
        self.pet._preferences.set_option("online_social", True)
        menu = self.menu()
        self.assertEqual(
            menu.buttons[SocialCategory.HOROSCOPE].cget("state"), "disabled"
        )
        self.assertIn("Sternzeichen", menu.status.cget("text"))
        menu.choose(SocialCategory.HOROSCOPE)
        self.assertEqual(self.pet._social_runtime.content.horoscope.attempts, 0)

    def test_restart_resumes_interrupted_bubble_without_second_care_or_http(self):
        item = self.begin()
        self.assertEqual(self.pet.state.social, 36)
        self.assertEqual(self.pet._speech.attribution, reading(item).footer)
        self.pet._reaction_player.advance_story()
        self.pet._reaction_player.advance_story()
        self.assertEqual(self.pet._social_runtime.content.horoscope.index, 2)
        self.pet._social_runtime.cancel()
        self.assertFalse(self.pet._reaction_player.active)
        self.assertEqual(self.pet._speech.attribution, "")
        store = self.pet.store
        self.pet.quit()
        self.worker = ManualSocialWorker(clock=self.worker.clock)
        reopened = create_test_desktop(store=store, social_worker=self.worker)
        self.addCleanup(reopened.quit)
        reopened._runtime.stop()
        reopened.settings.auto_routine = False
        reopened._reaction_player.cancel()
        reopened._action_playback.cancel_at(time.monotonic())
        self.assertFalse(reopened._reaction_player.story_active)
        self.assertEqual(reopened._social_runtime.content.horoscope.index, 2)
        before = reopened.state.social, reopened.state.energy, reopened.state.friendship
        reopened._social_runtime.select(SocialCategory.HOROSCOPE)
        reopened.root.update()
        self.assertEqual(reopened._reaction_player.cues[0], item.reaction.beats[0])
        self.assertEqual(
            reopened._reaction_player.cues[1].content, item.reaction.beats[2].content
        )
        self.assertEqual(
            (reopened.state.social, reopened.state.energy, reopened.state.friendship),
            before,
        )
        self.assertFalse(
            any(c == SocialCategory.HOROSCOPE for c, _ in self.worker.requests)
        )
        while reopened._reaction_player.story_active:
            reopened._reaction_player.advance_story()
        self.assertTrue(reopened._social_runtime.content.horoscope.completed)
        reopened._preferences.set_zodiac("leo")
        reopened._social_runtime.select(SocialCategory.HOROSCOPE)
        self.assertEqual(
            reopened._social_runtime.snapshot()[0],
            GERMAN_TEXT.format("social.horoscope.completed"),
        )
        saved = store.load_session()
        assert saved.social_history.horoscope is not None
        assert saved.social_history.horoscope.reading is not None
        self.assertTrue(saved.social_history.horoscope.completed)
        self.assertEqual(saved.social_history.horoscope.reading.sign, "aries")

    def test_opt_out_stops_role_and_reenable_resumes_without_care(self):
        self.begin()
        self.pet._reaction_player.advance_story()
        before = self.pet.state.social, self.pet.state.energy, self.pet.state.friendship
        self.pet._preferences.set_option("online_social", False)
        self.assertFalse(self.pet._reaction_player.story_active)
        self.assertEqual(self.pet._speech.attribution, "")
        day = self.pet._social_runtime.content.horoscope
        self.assertTrue(day.admitted)
        self.assertFalse(day.completed)
        self.pet._preferences.set_zodiac("leo")
        self.pet._preferences.set_option("online_social", True)
        self.pet._social_runtime.select(SocialCategory.HOROSCOPE)
        self.pet.root.update()
        self.assertTrue(self.pet._reaction_player.story_active)
        self.assertEqual(
            (self.pet.state.social, self.pet.state.energy, self.pet.state.friendship),
            before,
        )
        self.assertEqual(self.pet._social_runtime.content.horoscope.attempts, 1)

    def test_failed_admission_save_never_displays_or_books_care_again(self):
        self.pet._preferences.set_zodiac("aries")
        self.pet._preferences.set_option("online_social", True)
        self.menu().choose(SocialCategory.HOROSCOPE)
        self.pet.root.update()
        self.worker.complete(123)
        self.pet._social_runtime.poll()
        category, token = self.worker.requests[-1]
        assert isinstance(token, HoroscopeRequest)
        item = prepare_horoscope(horoscope_payload(token.sign, token.date), token)
        self.worker.result = SocialFetchResult(token, category, item)
        self.pet._social_runtime.poll()
        content = self.pet._social_runtime.content
        with patch.object(content, "_persist_requests", return_value=OSError("disk")):
            self.pet.root.update()
        self.assertFalse(self.pet._reaction_player.story_active)
        self.assertEqual(self.pet.state.social, 36)
        self.assertEqual(self.pet._speech.attribution, "")
        self.pet._social_runtime.select(SocialCategory.HOROSCOPE)
        self.pet.root.update()
        self.assertTrue(self.pet._reaction_player.story_active)
        self.assertEqual(self.pet.state.social, 36)
