"""Waiting, deferred admission and cancellation never create extra care."""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Callable
from unittest.mock import Mock

from test_social_coordinator import TEST_JOKE_CATALOG, ManualSocialWorker

from aiko_pet.application.social_candidates import JokeCatalog
from aiko_pet.application.social_content import PreparedSocialContent, SocialCategory
from aiko_pet.application.social_coordinator import SocialContentCoordinator
from aiko_pet.application.social_history import (
    SocialContentHistory,
    SocialContentReceipt,
)
from aiko_pet.desktop.social_runtime import (
    SocialConversationRuntime,
    SocialRuntimePorts,
)
from aiko_pet.pet.mind.catalog import Reaction


class SocialRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.worker = ManualSocialWorker()
        self.content = SocialContentCoordinator(
            self.worker, joke_catalog=TEST_JOKE_CATALOG, wall_time=self.worker.clock,
        )
        self.started: list[PreparedSocialContent] = []
        self.holding: list[Reaction] = []
        self.deferred: list[Callable[[], None]] = []
        self.allowed = True
        self.runtime = SocialConversationRuntime(self.content, SocialRuntimePorts(
            can_start=lambda: self.allowed, defer=self.deferred.append,
            start=self.start, show_wait=self.holding.append,
            clear_wait=self.holding.clear,
        ))
        self.runtime.set_enabled(True)

    def start(self, item: PreparedSocialContent) -> bool:
        self.started.append(item)
        return True

    def test_bounded_content_search_ends_holding_without_claiming_api_failure(self):
        self.runtime.select(SocialCategory.SINGLE)
        self.deferred.pop()()
        for _ in range(6):
            self.worker.complete(1)
            assert self.worker.result is not None
            self.worker.result = replace(
                self.worker.result, content=None, failure="invalid",
            )
            self.runtime.poll()
        self.assertFalse(self.runtime.waiting)
        self.assertFalse(self.holding)
        self.assertFalse(self.started)
        self.assertIn("Weitersuchen", self.runtime.snapshot()[0])
        self.assertEqual(self.content.history.entries, ())
        self.assertEqual(self.content.history.requests.blocks, ())

    def test_exhausted_small_pool_has_distinct_status_without_starting_playback(self):
        self.runtime.close()
        worker = ManualSocialWorker()
        content = SocialContentCoordinator(
            worker, wall_time=worker.clock,
            joke_catalog=JokeCatalog(0, 0, worker.clock() + 3600),
            history=SocialContentHistory((SocialContentReceipt(
                SocialCategory.TWO_PARTS, "jokeapi:0", "a" * 64,
            ),)),
        )
        runtime = SocialConversationRuntime(content, SocialRuntimePorts(
            can_start=lambda: True, defer=self.deferred.append,
            start=self.start, show_wait=self.holding.append,
            clear_wait=self.holding.clear,
        ))
        self.addCleanup(runtime.close)
        runtime.set_enabled(True)
        runtime.select(SocialCategory.TWO_PARTS)
        self.assertIn("keine passenden neuen Witze", runtime.snapshot()[0])
        self.assertFalse(runtime.waiting)
        self.assertFalse(self.holding)
        self.assertFalse(self.started)
        self.assertEqual(len(content.history.entries), 1)

    def test_wish_readiness_only_observes_existing_prepared_categories(self):
        self.assertEqual(self.runtime.prepared_categories, frozenset())
        self.worker.complete(1)
        self.runtime.poll()
        before = self.content.count(SocialCategory.SINGLE)
        for _ in range(2):
            self.assertEqual(self.runtime.prepared_categories, frozenset({"single"}))
        self.assertEqual(self.content.count(SocialCategory.SINGLE), before)
        self.assertFalse(self.runtime.waiting)
        self.assertFalse(self.started)
        self.runtime.set_enabled(False)
        self.assertEqual(self.runtime.prepared_categories, frozenset())

    def test_empty_buffer_holds_once_until_ready_without_awarding_early(self):
        self.runtime.select(SocialCategory.SINGLE)
        self.deferred.pop()()
        self.assertEqual(len(self.holding), 1)
        self.assertFalse(self.started)
        self.runtime.poll()
        self.assertEqual(len(self.holding), 1)
        self.worker.complete(1)
        self.runtime.poll()
        self.assertFalse(self.started)
        self.deferred.pop()()
        self.assertEqual(len(self.started), 1)
        self.assertFalse(self.runtime.waiting)
        self.assertFalse(self.holding)
        self.runtime.poll()
        self.assertEqual(len(self.started), 1)

    def test_ready_item_skips_holding_and_rechecks_before_deferred_start(self):
        self.worker.complete(1)
        self.runtime.poll()
        self.runtime.select(SocialCategory.SINGLE)
        self.assertFalse(self.holding)
        self.allowed = False
        self.deferred.pop()()
        self.assertFalse(self.started)

    def test_cancel_invalidates_both_holding_and_deferred_content(self) -> None:
        self.runtime.select(SocialCategory.SINGLE)
        waiting = self.deferred.pop()
        self.runtime.cancel()
        waiting()
        self.assertFalse(self.holding)
        self.worker.complete(1)
        self.runtime.poll()
        self.assertFalse(self.started)
        self.runtime.select(SocialCategory.SINGLE)
        begin = self.deferred.pop()
        self.runtime.cancel()
        begin()
        self.assertFalse(self.started)

    def test_fetch_failure_clears_holding_and_allows_explicit_retry(self) -> None:
        self.runtime.select(SocialCategory.SINGLE)
        self.deferred.pop()()
        self.worker.complete(1, fail=True)
        self.runtime.poll()
        self.assertTrue(self.runtime.waiting)
        self.worker.complete(2, fail=True)
        self.runtime.poll()
        self.assertFalse(self.holding)
        self.assertFalse(self.runtime.waiting)
        self.assertIn("erneuten", self.runtime.snapshot()[0])
        self.runtime.select(SocialCategory.SINGLE)
        self.assertFalse(self.runtime.waiting)
        self.assertIn("begrenzt", self.runtime.snapshot()[0])
        self.worker.clock.now += 60
        self.runtime.select(SocialCategory.SINGLE)
        self.assertTrue(self.runtime.waiting)

    def test_disabling_or_shutdown_invalidates_deferred_start(self) -> None:
        self.worker.complete(1)
        self.runtime.poll()
        self.runtime.select(SocialCategory.SINGLE)
        begin = self.deferred.pop()
        self.runtime.set_enabled(False)
        begin()
        self.runtime.close()
        self.assertFalse(self.started)
        self.assertFalse(self.runtime.waiting)
        self.assertTrue(self.worker.closed)

    def test_ready_before_wait_callback_skips_stale_holding_presentation(self):
        self.runtime.select(SocialCategory.SINGLE)
        wait = self.deferred.pop()
        self.worker.complete(1)
        self.runtime.poll()
        wait()
        self.assertFalse(self.holding)
        self.deferred.pop()()
        self.assertEqual(len(self.started), 1)

    def test_rejected_start_never_records_or_persists_admission(self):
        persisted = Mock()
        self.runtime._ports = replace(
            self.runtime._ports, start=lambda _item: False,
            persist_admission=persisted,
        )
        self.worker.complete(1)
        self.runtime.poll()
        self.runtime.select(SocialCategory.SINGLE)
        self.deferred.pop()()
        self.assertFalse(self.content.history.entries)
        persisted.assert_not_called()
