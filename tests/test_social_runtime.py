"""Waiting, deferred admission and cancellation never create extra care."""

from __future__ import annotations

import unittest
from typing import Callable

from test_social_coordinator import ManualSocialWorker

from aiko_pet.application.social_content import PreparedSocialContent, SocialCategory
from aiko_pet.application.social_coordinator import SocialContentCoordinator
from aiko_pet.desktop.social_runtime import (
    SocialConversationRuntime,
    SocialRuntimePorts,
)
from aiko_pet.pet.mind.catalog import Reaction


class SocialRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.worker = ManualSocialWorker()
        self.content = SocialContentCoordinator(self.worker)
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
        self.assertFalse(self.holding)
        self.assertFalse(self.runtime.waiting)
        self.assertIn("erneuten", self.runtime.snapshot()[0])
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
