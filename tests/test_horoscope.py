"""Horoscope provider contracts, durable daily admission and playback boundaries."""

from __future__ import annotations

import json
import unittest
from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock, patch

from test_social_api import HeaderResponse, http_headers
from test_social_coordinator import ManualSocialWorker

from aiko_pet.application.horoscope import prepare_horoscope
from aiko_pet.application.horoscope_models import HoroscopeRequest, HoroscopeText
from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_content import (
    PreparedSocialContent,
    SocialCategory,
    SocialProvider,
)
from aiko_pet.application.social_coordinator import (
    SocialContentCoordinator,
    SocialFetchResult,
)
from aiko_pet.application.social_history import SocialContentHistory
from aiko_pet.desktop.horoscope_playback import HoroscopePlayback
from aiko_pet.infrastructure.social_api import SocialFetchError, fetch_social_response
from aiko_pet.infrastructure.social_history_codec import (
    decode_social_history,
    encode_social_history,
)
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from aiko_pet.ui.pet_view.speech_presenter import SpeechPresenter
from tools.reaction_test_support import FakeScheduler


def horoscope_payload(sign: str = "aries", day: str = "2026-10-23") -> dict[str, Any]:
    # Provider-shaped fixture; never used as an offline/runtime fallback.
    return dict(
        ok=True,
        data=dict(
            sign=sign,
            date=day,
            period="daily",
            language="de",
            sections=dict(
                overview="Sie können heute Ihre Pläne in Ruhe ordnen. " * 5,
                advice="Nehmen Sie sich Zeit für Ihre Entscheidungen.",
            ),
            disclaimer=(
                "KI-generierter Text zur Unterhaltung. "
                "Keine wissenschaftliche Vorhersage."
            ),
        ),
        _footer="Powered by astroway.api - get your own key at https://api.astroway.info",
    )


def reading(item: PreparedSocialContent) -> HoroscopeText:
    assert item.horoscope is not None
    return item.horoscope


class HoroscopeContentTests(unittest.TestCase):
    def test_full_formal_content_and_disclaimer_fit_with_role_and_shared_timing(self):
        payload = horoscope_payload()
        item = prepare_horoscope(payload, HoroscopeRequest("aries", "2026-10-23"))
        beats = item.reaction.beats
        self.assertLessEqual(len(beats), 12)
        self.assertTrue(all(len(b.content) <= 125 for b in beats))
        joined = " ".join(b.content for b in beats[1:-1])
        self.assertIn(payload["data"]["disclaimer"], joined)
        for section in ("overview", "advice"):
            self.assertIn(
                " ".join(payload["data"]["sections"][section].split()), joined
            )
        self.assertIn("Sie", joined)
        self.assertIn("dein", beats[0].content)
        self.assertIn("deine Aiko", beats[-1].content)
        self.assertEqual(
            beats[-1].duration_ms,
            min(10000, max(4000, 1500 + 65 * len(beats[-1].content)) + 1000),
        )
        self.assertIsNone(item.reaction.completed_social)

    def test_oversized_missing_stale_english_and_mismatched_answers_rejected(self):
        base = horoscope_payload()
        cases = []
        for key, value in (
            ("date", "2026-10-22"),
            ("sign", "leo"),
            ("period", "weekly"),
            ("language", "en"),
            ("fallback", {"textDate": "2026-10-22"}),
        ):
            item = deepcopy(base)
            item["data"][key] = value
            cases.append(item)
        item = deepcopy(base)
        item["data"]["sections"]["overview"] = "Ein langer Satz. " * 100
        cases.append(item)
        item = deepcopy(base)
        item["data"].pop("disclaimer")
        cases.append(item)
        item = deepcopy(base)
        item.pop("_footer")
        cases.append(item)
        item = deepcopy(base)
        item["data"]["sections"].pop("advice")
        cases.append(item)
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                prepare_horoscope(payload, HoroscopeRequest("aries", "2026-10-23"))

    def test_public_http_has_no_key_and_rejects_stale_header(self):
        for stale in (False, True):
            response = HeaderResponse(json.dumps(horoscope_payload()).encode())
            response.headers = http_headers({"X-AI-Cache": "STALE"} if stale else {})
            with patch(
                "aiko_pet.infrastructure.social_api.urlopen", return_value=response
            ) as opened:
                request = HoroscopeRequest("aries", "2026-10-23")
                if stale:
                    with self.assertRaises(SocialFetchError):
                        fetch_social_response(
                            SocialCategory.HOROSCOPE, SocialProvider.ASTROWAY, request
                        )
                else:
                    fetch_social_response(
                        SocialCategory.HOROSCOPE, SocialProvider.ASTROWAY, request
                    )
                http = opened.call_args.args[0]
                self.assertEqual(
                    http.full_url,
                    "https://api.astroway.info/v1/public/horoscope/daily?sign=aries&lang=de&date=2026-10-23",
                )
                self.assertEqual(len(http.header_items()), 2)
                self.assertEqual(opened.call_args.kwargs["timeout"], 25)

    def test_settings_compatibility_and_sign_validation(self):
        self.assertIsNone(PetSettings.from_dict({}).zodiac_sign)
        self.assertIsNone(PetSettings.from_dict({"zodiac_sign": []}).zodiac_sign)
        settings = PetSettings(zodiac_sign="leo")
        self.assertEqual(PetSettings.from_dict(settings.to_dict()).zodiac_sign, "leo")
        with self.assertRaises(ValueError):
            settings.zodiac_sign = "not-a-sign"


class HoroscopeLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.worker = ManualSocialWorker()
        self.worker.clock.now = datetime(2026, 10, 23, 14).timestamp()
        self.sign: str | None = "aries"
        self.saved: list[SocialContentHistory] = []
        self.failure = False
        self.social = self.make_social()
        self.social.set_enabled(True)

    def make_social(self, history: SocialContentHistory = SocialContentHistory()):
        def persist():
            self.saved.append(self.social.history)
            return OSError("disk") if self.failure else None

        return SocialContentCoordinator(
            self.worker,
            history=history,
            wall_time=self.worker.clock,
            zodiac_sign=lambda: self.sign,
            persist_requests=persist,
        )

    def dispatch(self):
        self.assertEqual(self.social.select(SocialCategory.HOROSCOPE).status, "waiting")
        if self.worker.requests[-1][0] != SocialCategory.HOROSCOPE:
            self.worker.complete(111)
            self.social.poll()
        category, token = self.worker.requests[-1]
        self.assertEqual(category, SocialCategory.HOROSCOPE)
        return cast(HoroscopeRequest, token)

    def reply(self, token: HoroscopeRequest, *, fail: bool = False):
        item = (
            None
            if fail
            else prepare_horoscope(horoscope_payload(token.sign, token.date), token)
        )
        self.worker.result = SocialFetchResult(
            token, SocialCategory.HOROSCOPE, item, "invalid" if fail else None
        )
        return self.social.poll()

    def replied(self, token: HoroscopeRequest, *, fail: bool = False):
        result = self.reply(token, fail=fail)
        assert result is not None
        return result

    def prepared(self):
        token = self.dispatch()
        selection = self.reply(token)
        assert selection is not None and selection.content is not None
        return selection.content

    def test_opt_in_never_warms_horoscope_and_missing_sign_never_fetches(self):
        self.assertEqual(self.social.horoscope.attempts, 0)
        self.sign = None
        self.assertEqual(self.social.select(SocialCategory.HOROSCOPE).status, "sign")
        self.assertFalse(
            any(c == SocialCategory.HOROSCOPE for c, _ in self.worker.requests)
        )

    def test_three_dispatches_survive_restart_sign_changes_and_opt_out(self):
        for attempt in range(1, 4):
            token = self.dispatch()
            self.assertEqual(self.social.horoscope.attempts, attempt)
            saved_day = self.saved[-1].horoscope
            assert saved_day is not None
            self.assertEqual(saved_day.attempts, attempt)
            self.assertEqual(self.replied(token, fail=True).status, "error")
            history = decode_social_history(encode_social_history(self.social.history))
            self.social.set_enabled(False)
            self.sign = "leo"
            self.worker = ManualSocialWorker(clock=self.worker.clock)
            self.social = self.make_social(history)
            self.social.set_enabled(True)
            self.worker.clock.now += 61
        self.assertEqual(self.social.select(SocialCategory.HOROSCOPE).status, "limited")
        self.assertFalse(self.social.horoscope.completed)
        self.worker.clock.now += 86400
        self.assertEqual(self.social.horoscope.attempts, 0)

    def test_admission_care_once_resumes_without_fetch_and_completes_across_signs(self):
        item = self.prepared()
        care = Mock()
        self.assertTrue(self.social.admit_horoscope(item, care))
        self.social.accept(item)
        self.assertTrue(self.social.horoscope_progress(reading(item).date, 2))
        self.sign = "leo"
        requests = len(self.worker.requests)
        resumed = self.social.select(SocialCategory.HOROSCOPE).content
        assert resumed is not None
        self.assertEqual(resumed, item)
        self.assertTrue(self.social.admit_horoscope(resumed, care))
        care.assert_called_once()
        self.assertEqual(len(self.worker.requests), requests)
        self.social.horoscope_progress(
            reading(item).date, len(item.reaction.beats), completed=True
        )
        self.assertEqual(
            self.social.select(SocialCategory.HOROSCOPE).status, "completed"
        )
        self.assertEqual(
            decode_social_history(encode_social_history(self.social.history)),
            self.social.history,
        )

    def test_pre_admission_sign_change_and_late_day_response_are_rejected(self):
        token = self.dispatch()
        self.sign = "leo"
        self.assertEqual(self.replied(token).status, "error")
        self.assertIsNone(self.social.horoscope.reading)
        self.worker.clock.now += 61
        # Finish any ordinary refill, then dispatch a new explicit request.
        token = self.dispatch()
        self.worker.clock.now += 86400
        self.assertEqual(self.replied(token).status, "error")
        self.assertEqual(self.social.horoscope.attempts, 0)

    def test_no_http_on_failed_reservation_and_no_playback_on_failed_admission(self):
        self.failure = True
        before = len(self.worker.requests)
        self.social.select(SocialCategory.HOROSCOPE)
        self.worker.complete(111)
        self.social.poll()
        self.assertEqual(len(self.worker.requests), before)
        self.failure = False
        self.worker.clock.now += 61
        item = self.prepared()
        care = Mock()
        self.failure = True
        self.assertFalse(self.social.admit_horoscope(item, care))
        self.failure = False
        self.assertTrue(self.social.admit_horoscope(item, care))
        care.assert_called_once()

    def test_running_old_day_can_finish_but_paused_old_day_cannot_resume(self):
        item = self.prepared()
        self.social.admit_horoscope(item, lambda: None)
        self.social.accept(item)
        yesterday = reading(item).date
        self.worker.clock.now += 86400
        self.assertTrue(
            self.social.horoscope_progress(
                yesterday, len(item.reaction.beats), completed=True
            )
        )
        self.assertFalse(self.social.horoscope.completed)
        self.assertIsNone(self.social.horoscope.reading)

    def test_cached_episode_remains_available_after_third_attempt(self):
        item = self.prepared()
        self.social._history = replace(
            self.social.history, horoscope=replace(self.social.horoscope, attempts=3)
        )
        self.assertEqual(self.social.select(SocialCategory.HOROSCOPE).status, "ready")
        self.assertEqual(self.social.horoscope.reading, item.horoscope)

    def test_repeated_selection_joins_inflight_attempt_without_new_request(self):
        token = self.dispatch()
        for _ in range(4):
            self.assertEqual(
                self.social.select(SocialCategory.HOROSCOPE).status, "waiting"
            )
        self.assertEqual(self.social.horoscope.attempts, 1)
        self.assertEqual(self.replied(token).status, "ready")

    def test_cancelled_or_disabled_response_never_creates_reading(self):
        token = self.dispatch()
        self.social.cancel_selection()
        self.assertIsNone(self.reply(token))
        self.assertIsNone(self.social.horoscope.reading)
        self.assertEqual(self.social.horoscope.attempts, 1)

    def test_codec_rejects_inconsistent_progress_and_reads_v1_v2(self):
        self.prepared()
        raw = encode_social_history(self.social.history)
        for key, value in (
            ("attempts", 4),
            ("index", 13),
            ("admitted", 1),
            ("completed", True),
        ):
            bad = deepcopy(raw)
            bad["horoscope"][key] = value
            with self.assertRaises(ValueError):
                decode_social_history(bad)
        for version in (1, 2):
            old = {"version": version, "entries": []}
            if version == 2:
                old["requests"] = {"attempts": [], "blocks": []}
            self.assertIsNone(decode_social_history(old).horoscope)


class HoroscopePlaybackTests(unittest.TestCase):
    def test_resume_reintroduces_role_then_current_bubble_and_saves_before_display(
        self,
    ):
        scheduler = FakeScheduler()
        shown: list[str] = []
        progress: list[tuple[str, int, bool]] = []
        item = prepare_horoscope(
            horoscope_payload(), HoroscopeRequest("aries", "2026-10-23")
        )
        from aiko_pet.application.horoscope_models import HoroscopeDay

        day = HoroscopeDay("2026-10-23", 1, item.horoscope, 2, True)
        coordinator = Mock(spec=SocialContentCoordinator)
        coordinator.horoscope = day
        coordinator.admit_horoscope.return_value = True

        def save(date, index, *, completed=False):
            progress.append((date, index, completed))
            return True

        coordinator.horoscope_progress.side_effect = save
        player = ReactionPlayer(
            schedule=scheduler.schedule,
            cancel_timer=scheduler.cancel,
            display_emote=lambda *_a: None,
            display_text=lambda text, _duration: shown.append(text),
            start_action=lambda *_a: None,
            mark_spoken=lambda: None,
            is_closed=lambda: False,
        )
        speech = SimpleNamespace(attribution="")
        playback = HoroscopePlayback(
            coordinator, player, cast(SpeechPresenter, speech), Mock()
        )
        self.assertTrue(playback.start(item))
        self.assertEqual(shown, [item.reaction.beats[0].content])
        self.assertEqual(progress[-1][1], 2)
        self.assertEqual(speech.attribution, reading(item).footer)
        player.advance_story()
        self.assertEqual(shown[-1], item.reaction.beats[2].content)
        self.assertEqual(progress[-1][1], 2)
        while player.story_active:
            player.advance_story()
        self.assertEqual(progress[-1], (day.date, len(item.reaction.beats), True))
        self.assertFalse(playback.active)
        self.assertEqual(speech.attribution, "")
        self.assertNotIn(item.reaction.beats[1].content, shown)

    def test_failed_progress_save_cancels_before_presenting_text(self):
        scheduler = FakeScheduler()
        shown = []
        player = ReactionPlayer(
            schedule=scheduler.schedule,
            cancel_timer=scheduler.cancel,
            display_emote=lambda *_a: None,
            display_text=lambda *_a: shown.append(True),
            start_action=lambda *_a: None,
            mark_spoken=lambda: None,
            is_closed=lambda: False,
        )
        item = prepare_horoscope(
            horoscope_payload(), HoroscopeRequest("aries", "2026-10-23")
        )
        completed = []
        player.play(
            item.reaction, on_progress=lambda _i: False, on_complete=completed.append
        )
        self.assertFalse(shown)
        self.assertEqual(completed, [False])
        self.assertFalse(player.active)
