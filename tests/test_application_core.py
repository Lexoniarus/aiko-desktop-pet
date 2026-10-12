"""Headless application boundary and future integration contract tests."""

from __future__ import annotations

import random
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from aiko_pet.adaptive import AdaptiveRoutine
from aiko_pet.application.commands import CareCommand, NotificationCommand
from aiko_pet.application.controller import CareController, CareRuntime
from aiko_pet.application.events import IncomingNotification
from aiko_pet.application.inbox import NotificationInbox
from aiko_pet.application.router import ApplicationRouter
from aiko_pet.dialogue import AikoMind
from aiko_pet.domain import PetState


def runtime(*, wall_time: float | None = None) -> CareRuntime:
    return CareRuntime(
        wall_time=(
            wall_time if wall_time is not None
            else datetime(2026, 10, 13, 16).timestamp()
        ),
        monotonic_time=2000.0,
        auto_routine=False,
        allow_bedtime=None,
        allow_nap=False,
        interrupt_nap=False,
        effort=None,
    )


def notification(identifier: str = "test-1") -> IncomingNotification:
    return IncomingNotification(
        event_id=identifier, source="test.integration",
        title="Termin", message="In zehn Minuten.",
    )


class ApplicationCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = PetState()
        self.mind = AikoMind(rng=random.Random(8))
        self.adaptive = AdaptiveRoutine()
        self.router = ApplicationRouter(
            CareController(self.state, self.mind, self.adaptive),
            NotificationInbox(capacity=2),
        )

    def test_care_uses_pre_action_tone_and_preserves_state_schema(self) -> None:
        initial_keys = set(self.state.to_dict())
        self.state.affection = 10.0
        result = self.router.dispatch(CareCommand("pet"), runtime=runtime())
        self.assertEqual(self.state.affection, 35.0)
        self.assertEqual(result.context.day_key, "2026-10-13")
        self.assertEqual(set(self.state.to_dict()), initial_keys)
        self.assertEqual(self.adaptive.memory.last_contact_wall,
                         runtime().wall_time)
        self.assertIsNotNone(result.reaction)

    def test_care_matches_prior_pet_dialogue_order(self) -> None:
        rt = runtime()
        state = PetState(social=10.0)
        mind = AikoMind(rng=random.Random(12))
        controller = CareController(state, mind, AdaptiveRoutine())
        outcome = controller.execute(CareCommand("talk"), rt)
        self.assertEqual(state.social, 36.0)
        self.assertIsNotNone(outcome.reaction)
        self.assertEqual(mind._last_care_action, "talk")
        self.assertEqual(mind._last_care_at, rt.monotonic_time)

    def test_invalid_commands_never_mutate_aiko(self) -> None:
        before = self.state.to_dict()
        with self.assertRaises(ValueError):
            CareCommand("unknown")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            self.router.dispatch(CareCommand("pet"))
        self.assertEqual(self.state.to_dict(), before)

    def test_worker_thread_cannot_modify_pet_state(self) -> None:
        before = self.state.to_dict()
        with ThreadPoolExecutor(max_workers=1) as pool:
            attempt = pool.submit(
                self.router.dispatch, CareCommand("pet"), runtime=runtime(),
            )
            with self.assertRaises(RuntimeError):
                attempt.result()
        self.assertEqual(self.state.to_dict(), before)

    def test_notification_can_be_enqueued_from_another_thread(self) -> None:
        with ThreadPoolExecutor(max_workers=1) as pool:
            receipt = pool.submit(
                self.router.dispatch, NotificationCommand(notification()),
            ).result()
        self.assertEqual(receipt.status, "accepted")
        self.assertEqual(
            self.router.next_notification(),
            notification(),
        )

    def test_queue_is_bounded_and_duplicate_requests_are_idempotent(self) -> None:
        first = NotificationCommand(notification("n-1"))
        self.assertEqual(self.router.dispatch(first).status, "accepted")
        self.assertEqual(self.router.dispatch(first).status, "duplicate")
        self.router.dispatch(NotificationCommand(notification("n-2")))
        self.assertEqual(
            self.router.dispatch(NotificationCommand(notification("n-3"))).status,
            "full",
        )
        self.assertEqual(self.router.next_notification(), notification("n-1"))
        self.assertEqual(self.router.dispatch(first).status, "duplicate")
        self.assertEqual(self.router.next_notification(), notification("n-2"))
        self.assertIsNone(self.router.next_notification())

    def test_untrusted_notification_payload_is_validated(self) -> None:
        data: dict[str, object] = {
            "version": 1, "type": "notification.created", "id": "event-2",
            "title": "Kalender", "message": "Termin in zehn Minuten.",
            "priority": "normal",
        }
        received = IncomingNotification.from_payload(
            data, authenticated_source="browser.extension",
        )
        self.assertEqual(received.source, "browser.extension")
        for key, value in (
            ("version", 2), ("type", "care.execute"),
            ("id", "../unsafe"), ("message", "bad\x00control"),
            ("priority", "critical"),
        ):
            with self.subTest(key=key):
                changed = dict(data)
                changed[key] = value
                with self.assertRaises(ValueError):
                    IncomingNotification.from_payload(
                        changed, authenticated_source="browser.extension",
                    )
        with self.assertRaises(ValueError):
            IncomingNotification.from_payload(
                dict(data, source="untrusted"), authenticated_source="real",
            )

    def test_shutdown_rejects_future_notifications(self) -> None:
        self.router.close()
        receipt = self.router.dispatch(NotificationCommand(notification()))
        self.assertEqual(receipt.status, "full")
        self.assertIsNone(self.router.next_notification())


if __name__ == "__main__":
    unittest.main()
