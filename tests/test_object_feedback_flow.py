"""Headless integration of required object feedback and search readiness."""

import unittest
from dataclasses import replace
from typing import NoReturn
from unittest.mock import patch

from aiko_pet.application.object_feedback import FeedbackReceipt, ObjectFeedback
from aiko_pet.application.object_interaction import ObjectInteractionCoordinator
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.pet.mind.catalog import DialogueBook, Reaction
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.ui.pet_view.object_feedback_presenter import ObjectFeedbackPresenter
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from aiko_pet.world.contracts import WorldSurface
from aiko_pet.world.state import WorldState
from tools.reaction_test_support import FakeScheduler


class ObjectFeedbackFlowTests(unittest.TestCase):
    def test_different_same_kind_find_announces_reunion_only_after_identification(self):
        self.memory.update(
            (
                ObjectObservation(
                    "old",
                    "onigiri",
                    "food",
                    100,
                    0,
                    True,
                    0,
                ),
            ),
            now=0,
        )
        self.memory.mark_assessed("old")
        self.memory.note_placement("old", x=100, height=0, now=0, deferred=True)
        self.memory.restore_snapshot(
            tuple(
                replace(item, instance_id="object_1") for item in self.memory.snapshot()
            )
        )
        self.memory.mark_missing("old")
        subject = self.memory.get("old")
        assert subject is not None
        self.coordinator.notice_absence(subject)
        for _ in range(2):
            token = self.player.pending_timer
            assert token is not None
            self.scheduler.fire(token)
            self.coordinator.update()
        self.assertTrue(self.coordinator.search_ready)
        found = self.memory.observe_find(
            ObjectObservation(
                "sighting",
                None,
                None,
                600,
                0,
                True,
                1,
            ),
            now=1,
            record=None,
            claimed=frozenset(),
            maximum_distance=25,
            instance_id="object_3",
        )
        self.assertFalse(self.coordinator.found(found))
        self.assertNotIn("object_found", [cue.event for cue in self.presented])
        self.memory.observe_find(
            ObjectObservation(
                "sighting",
                "onigiri",
                "food",
                600,
                80,
                False,
                2,
            ),
            now=2,
            record=found,
            claimed=frozenset(),
            maximum_distance=25,
            preserve_record=True,
            instance_id="object_3",
        )
        world = self.world.snapshot()
        self.assertTrue(self.coordinator.found(found))
        self.assertEqual(self.presented[-1].event, "object_found")
        self.assertEqual(self.presented[-1].record_id, found)
        self.assertIn("Onigiri", self.visible[-1][0])
        self.assertIsNone(self.memory.get("old"))
        known = self.memory.get(found)
        assert known is not None
        self.assertTrue(known.assessed)
        self.assertEqual(known.disposition, "deferred")
        self.assertEqual(known.instance_id, "object_3")
        self.assertEqual(self.world.snapshot(), world)
        self.assertFalse(self.coordinator.found(found))
        self.assertEqual([cue.event for cue in self.presented].count("object_found"), 1)
        # This feedback-only fixture has no physical completion/abort adapters.
        with patch.object(self.coordinator, "receive_feedback"):
            self.player.cancel()

    def setUp(self) -> None:
        self.world = WorldState(WorldSurface(800, 600), ())
        self.memory = ObjectMemory()
        self.scheduler = FakeScheduler()
        self.visible: list[tuple[str, int]] = []
        self.receipts: list[FeedbackReceipt] = []
        self.presented: list[ObjectFeedback] = []

        def unexpected_effect(*_args: object) -> NoReturn:
            self.fail("Feedback playback must not perform a physical item action")

        self.player = ReactionPlayer(
            schedule=self.scheduler.schedule,
            cancel_timer=self.scheduler.cancel,
            display_text=lambda text, ms: self.visible.append((text, ms)),
            display_emote=lambda _text, _ms: None,
            start_action=unexpected_effect,
            mark_spoken=lambda: None,
            is_closed=lambda: False,
        )
        self.addCleanup(self.player.cancel)
        self.presenter = ObjectFeedbackPresenter(self.player, load_item_catalog())
        self.book = DialogueBook.from_file()
        self.coordinator = ObjectInteractionCoordinator(
            self.world,
            memory=self.memory,
            play=unexpected_effect,
            stop=lambda: None,
            select_item=unexpected_effect,
            consume=unexpected_effect,
            can_acquire=unexpected_effect,
            ground_x=unexpected_effect,
            hand_type_conflicts=unexpected_effect,
            completed=unexpected_effect,
            decide=unexpected_effect,
            resolve_instance=lambda _record: None,
            record_for_instance=lambda _instance: None,
            feedback=self.present,
            cancel_feedback=self.player.cancel,
            now=lambda: 0,
            inspection_seconds=0,
        )

    def received(self, receipt: FeedbackReceipt) -> None:
        self.receipts.append(receipt)
        self.coordinator.receive_feedback(receipt)

    def present(self, cue: ObjectFeedback) -> None:
        self.presented.append(cue)
        line = next(
            line
            for line in self.book.lines
            if line.event == cue.event
            and not line.conditions
            and not line.periods
            and not line.weekdays
        )
        self.presenter.show(
            cue,
            Reaction(line.id, line.beats, line.animation, line.event),
            self.received,
        )

    def test_named_losses_wait_for_presented_text_before_search_is_ready(self):
        # Geometry and orientation admit these confirmed losses upstream.
        records = []
        for identity in ("dango", "energy_drink", "onigiri"):
            self.memory.update(
                (
                    ObjectObservation(
                        identity,
                        identity,
                        "drink" if identity == "energy_drink" else "food",
                        100,
                        0,
                        True,
                        0,
                    ),
                ),
                now=0,
            )
            self.memory.mark_missing(identity)
            known = self.memory.get(identity)
            assert known is not None
            records.append(known.token)
            self.assertTrue(self.coordinator.notice_absence(known))

        for index, expected in enumerate(("Dango", "Energy", "Onigiri", None)):
            self.coordinator.update()
            self.assertTrue(self.coordinator.search_active)
            self.assertFalse(self.coordinator.search_ready)
            self.assertEqual(len(self.presented), index + 1)
            cue = self.presented[-1]
            self.assertEqual(
                cue.event, "object_place_missing" if expected else "object_search"
            )
            if expected:
                self.assertIn(expected, self.visible[-1][0])
                self.assertEqual(cue.record_id, records[index])
            token = self.player.pending_timer
            assert token is not None
            delay, stale = self.scheduler.callbacks[token]
            self.assertGreaterEqual(delay, 1800)
            self.assertEqual(delay, self.visible[-1][1])
            # Ordinary updates cannot skip readable text; a previous completion
            # cannot satisfy the newly presented required cue.
            self.coordinator.update()
            self.assertEqual(self.player.pending_timer, token)
            if self.receipts:
                self.coordinator.receive_feedback(self.receipts[-1])
                self.assertFalse(self.coordinator.search_ready)
            self.scheduler.fire(token)
            self.coordinator.update()
            current_timer = self.player.pending_timer
            stale()
            self.assertEqual(self.player.pending_timer, current_timer)
            self.assertEqual(len(self.receipts), index + 1)
        self.assertTrue(self.coordinator.search_ready)
        self.assertEqual(len({cue.key for cue in self.presented}), 4)
        self.assertTrue(all(receipt.completed for receipt in self.receipts))
        self.assertEqual(self.world.snapshot().objects, ())
