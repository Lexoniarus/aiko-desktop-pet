"""Finite budgets, real save/restart boundaries and bounded refill failure."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_social_coordinator import ManualSocialWorker

from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_content import SocialCategory, SocialProvider
from aiko_pet.application.social_coordinator import SocialContentCoordinator
from aiko_pet.application.social_history import SocialContentHistory
from aiko_pet.application.social_requests import (
    REQUEST_CAPS,
    SocialRequestHistory,
    SocialRequestReceipt,
)
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.social_history_codec import (
    decode_social_history,
    encode_social_history,
)
from aiko_pet.pet.state import PetState


class SocialRequestPolicyTests(unittest.TestCase):
    def test_each_provider_has_independent_pacing_and_rolling_hour_cap(self):
        for provider, (interval, hourly, _daily) in REQUEST_CAPS.items():
            history = SocialRequestHistory()
            for index in range(hourly):
                history = history.reserved(provider, 100000 + index * interval)
            self.assertEqual(
                history.ready_at(provider, 100000 + hourly * interval), 103600
            )
            with self.assertRaises(ValueError):
                history.reserved(provider, 100000 + hourly * interval)
            history.reserved(provider, 103600)
            other = next(p for p in SocialProvider if p != provider)
            self.assertEqual(history.ready_at(other, 100000), 100000)

    def test_rolling_day_cap_is_not_a_calendar_midnight_reset(self):
        for provider, (interval, hourly, daily) in REQUEST_CAPS.items():
            history = SocialRequestHistory()
            stamp = 100000
            for index in range(daily):
                stamp = 100000 + (index // hourly) * 3600 + (index % hourly) * interval
                history = history.reserved(provider, stamp)
            self.assertEqual(history.ready_at(provider, stamp + interval), 186400)
            history.reserved(provider, 186400)

    def test_expiry_and_clock_rollback_never_make_future_attempts_eligible(self):
        provider = SocialProvider.QUOTATIONS
        history = SocialRequestHistory().reserved(provider, 100000)
        self.assertEqual(history.ready_at(provider, 99900), 100010)
        self.assertEqual(history.pruned(186400), SocialRequestHistory())
        blocked = history.blocked(provider, 200000).blocked(provider, 110000)
        self.assertEqual(blocked.ready_at(provider, 100000), 200000)
        self.assertFalse(blocked.pruned(200000).blocks)

    def test_request_metadata_roundtrips_and_old_receipts_remain_readable(self):
        history = SocialContentHistory(
            requests=SocialRequestHistory()
            .reserved(
                SocialProvider.JOKEAPI,
                100000,
            )
            .blocked(SocialProvider.JOKEAPI, 101000)
        )
        raw = encode_social_history(history)
        self.assertEqual(raw["version"], 3)
        self.assertEqual(decode_social_history(raw), history)
        self.assertEqual(
            decode_social_history(dict(version=1, entries=[])), SocialContentHistory()
        )

    def test_malformed_and_unbounded_request_metadata_is_rejected(self):
        for requests in (
            dict(attempts=[], blocks=[dict(provider="other", until=1000)]),
            dict(attempts=[dict(provider="jokeapi", at=True)], blocks=[]),
            dict(attempts=[dict(provider="jokeapi", at=float("nan"))], blocks=[]),
            dict(attempts=[dict(provider="jokeapi", at=-1)], blocks=[]),
            dict(attempts=[dict(provider="jokeapi", at=1000)] * 301, blocks=[]),
            dict(attempts=[], blocks=[dict(provider="jokeapi", until=1000)] * 2),
        ):
            with self.subTest(requests=requests):
                with self.assertRaises(ValueError):
                    decode_social_history(
                        dict(version=2, entries=[], requests=requests)
                    )


class RequestAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.worker = ManualSocialWorker()
        self.content = SocialContentCoordinator(
            self.worker, wall_time=self.worker.clock
        )

    def invalid(self):
        self.worker.complete(1)
        assert self.worker.result is not None
        self.worker.result = replace(
            self.worker.result, content=None, failure="invalid"
        )
        return self.content.poll()

    def test_six_rejections_stop_both_saying_sources_and_toggle_does_not_reset(self):
        self.content.set_enabled(True)
        self.content.select(SocialCategory.SINGLE)
        for _ in range(5):
            self.assertIsNone(self.invalid())
            # Repeated clicks join existing work and do not reset retry accounting.
            self.content.select(SocialCategory.SINGLE)
        result = self.invalid()
        assert result is not None
        self.assertEqual(result.status, "limited")
        for provider in (SocialProvider.JOKEAPI, SocialProvider.QUOTATIONS):
            self.assertEqual(self.worker.providers.count(provider), 3)
        history = self.content.history
        self.content.set_enabled(False)
        self.content.set_enabled(True)
        self.assertEqual(self.content.history, history)
        self.assertEqual(self.content.select(SocialCategory.SINGLE).status, "limited")

    def test_reservation_is_saved_before_dispatch_and_survives_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            store = StateStore(Path(folder) / "state.json")
            pet = PetState(updated_at=self.worker.clock())

            def persist():
                self.assertFalse(self.worker.requests)
                store.save(pet, PetSettings(), social_history=self.content.history)
                return None

            self.content = SocialContentCoordinator(
                self.worker,
                wall_time=self.worker.clock,
                persist_requests=persist,
            )
            self.content.set_enabled(True)
            loaded = store.load_session(now=self.worker.clock())
            self.assertEqual(len(loaded.social_history.requests.attempts), 1)
            self.assertEqual(
                loaded.state.capture_checkpoint(), pet.capture_checkpoint()
            )
            other = ManualSocialWorker(clock=self.worker.clock)
            restarted = SocialContentCoordinator(
                other, history=loaded.social_history, wall_time=other.clock
            )
            restarted.set_enabled(True)
            self.assertEqual(other.providers, [SocialProvider.QUOTATIONS])

    def test_failed_save_forbids_http_and_reports_unavailable(self):
        self.content = SocialContentCoordinator(
            self.worker,
            wall_time=self.worker.clock,
            persist_requests=lambda: OSError("test save failure"),
        )
        self.content.set_enabled(True)
        self.assertFalse(self.worker.requests)
        self.assertEqual(self.content.select(SocialCategory.SINGLE).status, "error")
        self.assertFalse(self.worker.requests)
        self.assertFalse(self.content.history.entries)

    def test_provider_block_from_disabled_response_still_prevents_future_requests(self):
        self.content.set_enabled(True)
        self.content.set_enabled(False)
        self.worker.complete(1, fail=True)
        assert self.worker.result is not None
        self.worker.result = replace(
            self.worker.result, failure="rate", retry_at=self.worker.clock() + 900
        )
        self.content.poll()
        self.assertGreater(
            self.content.history.requests.ready_at(
                SocialProvider.JOKEAPI,
                self.worker.clock(),
            ),
            self.worker.clock(),
        )
        self.content.set_enabled(True)
        self.assertEqual(self.worker.providers[-1], SocialProvider.QUOTATIONS)
        self.assertFalse(self.content.history.entries)

    def test_both_joke_actions_share_one_provider_reservation_budget(self):
        now = self.worker.clock()
        exhausted = SocialRequestHistory(
            tuple(
                SocialRequestReceipt(SocialProvider.JOKEAPI, now - 300 + i * 5)
                for i in range(60)
            )
        )
        self.content = SocialContentCoordinator(
            self.worker,
            wall_time=self.worker.clock,
            history=SocialContentHistory(requests=exhausted),
        )
        self.content.set_enabled(True)
        self.assertEqual(self.worker.providers, [SocialProvider.QUOTATIONS])
        self.assertEqual(
            self.content.select(SocialCategory.TWO_PARTS).status, "limited"
        )
        self.assertEqual(self.content.select(SocialCategory.SINGLE).status, "waiting")
