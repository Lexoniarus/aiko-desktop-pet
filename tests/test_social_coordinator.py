"""Individual preparation, independent buffers and stale-result isolation."""

from __future__ import annotations

import unittest

from test_social_content import fact_payload, joke_payload

from aiko_pet.application.social_content import (
    BUFFERED_CATEGORIES,
    SocialCategory,
    SocialProvider,
    default_provider,
    prepare_social_content,
)
from aiko_pet.application.social_coordinator import SocialContentCoordinator
from aiko_pet.application.social_fetch import SocialFetchRequest, SocialFetchResult


class SocialTestClock:
    def __init__(self) -> None:
        self.now = 1800000000.0

    def __call__(self) -> float:
        return self.now


class ManualSocialWorker:
    def __init__(self, *, clock: SocialTestClock | None = None) -> None:
        self.requests: list[tuple[SocialCategory, object]] = []
        self.providers: list[SocialProvider] = []
        self.clock = clock or SocialTestClock()
        self.result: SocialFetchResult | None = None
        self.closed = False
        self.plans: list[SocialFetchRequest | None] = []

    def start(self, category: SocialCategory, token: object,
              provider: SocialProvider | None = None, *,
              request: SocialFetchRequest | None = None) -> None:
        self.plans.append(request)
        self.requests.append((category, token))
        self.providers.append(provider or default_provider(category))

    def poll(self) -> SocialFetchResult | None:
        result, self.result = self.result, None
        return result

    def complete(self, identifier: int, *, fail: bool = False) -> None:
        category, token = self.requests[-1]
        provider = self.providers[-1]
        payload = (fact_payload(str(identifier)) if category == SocialCategory.FACT
                   else joke_payload(category, identifier))
        # Distinct content, not just distinct provider IDs.
        field = ("text" if category == SocialCategory.FACT else "joke"
                 if category == SocialCategory.SINGLE else "setup")
        payload[field] = f"Test {identifier}."
        if provider == SocialProvider.QUOTATIONS:
            payload = dict(quote=f"Test {identifier}.", language="de",
                           link=f"https://www.zitat-service.de/de/quotations/{identifier}",
                           authorName="Testautor")
        content = (None if fail else prepare_social_content(
            category, payload, provider=provider,
        ))
        self.clock.now += 10
        self.result = SocialFetchResult(
            token, category, content, failure="temporary" if fail else None,
            retry_at=self.clock.now + 60 if fail else None,
        )

    def close(self) -> None:
        self.closed = True


class SocialCoordinatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.worker = ManualSocialWorker()
        self.social = SocialContentCoordinator(self.worker, wall_time=self.worker.clock)

    def test_opt_in_individually_fills_two_slots_for_each_category(self) -> None:
        self.assertFalse(self.worker.requests)
        self.social.set_enabled(True)
        for identifier in range(6):
            self.assertEqual(len(self.worker.requests), identifier + 1)
            self.worker.complete(identifier)
            self.assertIsNone(self.social.poll())
        self.assertEqual(len(self.worker.requests), 6)
        for category in BUFFERED_CATEGORIES:
            self.assertEqual(self.social.count(category), 2)
        selected = self.social.select(SocialCategory.FACT)
        self.assertEqual(selected.status, "ready")
        self.assertEqual(self.social.count(SocialCategory.FACT), 1)
        self.assertEqual(len(self.worker.requests), 7)

    def test_empty_selection_joins_matching_fetch_and_delivers_first_ready(self):
        self.social.set_enabled(True)
        self.assertEqual(self.social.select(SocialCategory.SINGLE).status, "waiting")
        self.assertEqual(len(self.worker.requests), 1)
        self.worker.complete(5)
        update = self.social.poll()
        assert update is not None
        self.assertEqual(update.status, "ready")
        self.assertEqual(self.social.count(SocialCategory.SINGLE), 0)
        self.assertFalse(self.social.waiting)

    def test_waiting_category_takes_priority_after_other_fetch_finishes(self):
        self.social.set_enabled(True)
        self.social.select(SocialCategory.FACT)
        self.worker.complete(1)
        self.social.poll()
        self.assertEqual(self.worker.requests[-1][0], SocialCategory.FACT)

    def test_disable_reenable_drops_old_generation_without_parallel_fetches(self):
        self.social.set_enabled(True)
        self.social.select(SocialCategory.SINGLE)
        self.social.set_enabled(False)
        self.social.set_enabled(True)
        self.assertEqual(len(self.worker.requests), 1)
        self.worker.complete(1)
        self.assertIsNone(self.social.poll())
        self.assertEqual(self.social.count(SocialCategory.SINGLE), 0)
        self.assertEqual(len(self.worker.requests), 2)

    def test_cancelled_waiter_never_autoplays_but_background_warming_continues(self):
        self.social.set_enabled(True)
        self.social.select(SocialCategory.SINGLE)
        self.social.cancel_selection()
        self.worker.complete(1)
        self.assertIsNone(self.social.poll())
        self.assertEqual(self.social.count(SocialCategory.SINGLE), 1)

    def test_failure_is_reported_once_and_does_not_loop_failed_category(self):
        self.social.set_enabled(True)
        self.social.select(SocialCategory.SINGLE)
        self.worker.complete(1, fail=True)
        update = self.social.poll()
        self.assertIsNone(update)  # The second Sprüche source is still available.
        self.assertEqual(self.worker.providers[-1], SocialProvider.QUOTATIONS)
        self.worker.complete(2, fail=True)
        update = self.social.poll()
        assert update is not None
        self.assertEqual(update.status, "error")
        self.assertFalse(self.social.waiting)
        self.assertNotEqual(self.worker.requests[-1][0], SocialCategory.SINGLE)
        self.assertIsNone(self.social.poll())

    def test_duplicate_ready_and_recent_content_never_fills_a_second_slot(self):
        self.social.set_enabled(True)
        for identifier in range(3):
            self.worker.complete(identifier)
            self.social.poll()
        self.worker.complete(0)
        self.social.poll()
        self.assertEqual(self.social.count(SocialCategory.SINGLE), 1)
        selected = self.social.select(SocialCategory.SINGLE)
        assert selected.content is not None
        self.social.accept(selected.content)
        self.assertEqual(self.social.count(SocialCategory.SINGLE), 0)

    def test_close_clears_buffers_and_never_requests_again(self) -> None:
        self.social.set_enabled(True)
        self.social.close()
        self.worker.complete(1)
        self.assertIsNone(self.social.poll())
        self.assertTrue(self.worker.closed)
        self.assertEqual(self.social.select(SocialCategory.SINGLE).status, "disabled")
        self.social.set_enabled(True)
        self.assertEqual(len(self.worker.requests), 1)

    def test_offer_is_reserved_until_acceptance_and_cannot_be_accepted_twice(self):
        self.social.set_enabled(True)
        self.social.select(SocialCategory.SINGLE)
        self.worker.complete(1)
        offered = self.social.poll()
        assert offered is not None and offered.content is not None
        # Refill is already in flight before deferred playback begins.
        self.worker.complete(1)
        self.social.poll()
        self.assertEqual(self.social.count(SocialCategory.SINGLE), 0)
        self.social.accept(offered.content)
        with self.assertRaises(ValueError):
            self.social.accept(offered.content)

    def test_cancelled_offer_is_not_recorded_as_delivered(self) -> None:
        self.social.set_enabled(True)
        self.social.select(SocialCategory.SINGLE)
        self.worker.complete(1)
        offered = self.social.poll()
        assert offered is not None and offered.content is not None
        self.social.cancel_selection()
        with self.assertRaises(ValueError):
            self.social.accept(offered.content)

    def test_duplicates_retry_individually_then_report_failure_at_the_bound(self):
        self.social.set_enabled(True)
        self.social.select(SocialCategory.SINGLE)
        self.worker.complete(1)
        offered = self.social.poll()
        assert offered is not None and offered.content is not None
        self.social.accept(offered.content)
        self.social.select(SocialCategory.SINGLE)
        for _ in range(5):
            self.worker.complete(1)
            self.assertIsNone(self.social.poll())
            self.assertTrue(self.social.waiting)
            self.assertEqual(self.worker.requests[-1][0], SocialCategory.SINGLE)
        self.worker.complete(1)
        update = self.social.poll()
        assert update is not None
        self.assertEqual(update.status, "error")
        self.assertFalse(self.social.waiting)
        self.assertNotEqual(self.worker.requests[-1][0], SocialCategory.SINGLE)

    def test_old_deliveries_become_eligible_after_one_hundred_newer_items(self) -> None:
        self.social.set_enabled(True)
        for identifier in (*range(1, 102), 1):
            self.worker.clock.now += 3600  # This case checks retention, not quotas.
            self.social.select(SocialCategory.SINGLE)
            self.worker.complete(identifier)
            update = self.social.poll()
            assert update is not None and update.content is not None
            self.assertEqual(update.status, "ready")
            self.social.accept(update.content)

    def test_all_hundred_receipts_block_ids_and_content_across_categories(self):
        self.social.set_enabled(True)
        for identifier in range(1, 101):
            self.worker.clock.now += 3600
            self.social.select(SocialCategory.SINGLE)
            self.worker.complete(identifier)
            offered = self.social.poll()
            assert offered is not None and offered.content is not None
            self.social.accept(offered.content)
        history = self.social.history
        self.assertEqual(len(history.entries), 100)
        worker = ManualSocialWorker()
        restored = SocialContentCoordinator(worker, history=history,
                                            wall_time=worker.clock)
        for entry in history.entries:
            # Same namespaced provider ID, different words and category.
            payload = joke_payload(SocialCategory.TWO_PARTS,
                                   int(entry.identity.split(":")[1]))
            item = prepare_social_content(SocialCategory.TWO_PARTS, payload)
            self.assertTrue(restored._duplicate(item))
            # Changed ID/provider, normalized words still match.
            payload = fact_payload("new")
            payload["text"] = "  TEST   " + entry.identity.split(":")[1] + ".  "
            self.assertTrue(restored._duplicate(
                prepare_social_content(SocialCategory.FACT, payload),
            ))
        self.assertEqual(restored.history, history)
        self.social.set_enabled(False)
        self.social.set_enabled(True)
        self.assertEqual(self.social.history, history)

    def test_unaccepted_content_and_cancellation_do_not_write_receipts(self):
        self.social.set_enabled(True)
        self.worker.complete(1)
        self.social.poll()
        self.assertFalse(self.social.history.entries)
        offered = self.social.select(SocialCategory.SINGLE)
        assert offered.content is not None
        self.assertFalse(self.social.history.entries)
        self.social.cancel_selection()
        with self.assertRaises(ValueError):
            self.social.accept(offered.content)
        self.assertFalse(self.social.history.entries)
