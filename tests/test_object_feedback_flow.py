"""Headless integration of required object feedback and search readiness."""

import unittest
from typing import NoReturn

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
            schedule=self.scheduler.schedule, cancel_timer=self.scheduler.cancel,
            display_text=lambda text, ms: self.visible.append((text, ms)),
            display_emote=lambda _text, _ms: None,
            start_action=unexpected_effect,
            mark_spoken=lambda: None, is_closed=lambda: False,
        )
        self.addCleanup(self.player.cancel)
        self.presenter = ObjectFeedbackPresenter(self.player, load_item_catalog())
        self.book = DialogueBook.from_file()
        self.coordinator = ObjectInteractionCoordinator(
            self.world, memory=self.memory,
            play=unexpected_effect, stop=lambda: None, select_item=unexpected_effect,
            consume=unexpected_effect, can_acquire=unexpected_effect,
            ground_x=unexpected_effect, hand_type_conflicts=unexpected_effect,
            completed=unexpected_effect, decide=unexpected_effect,
            resolve_instance=lambda _record: None,
            record_for_instance=lambda _instance: None,
            feedback=self.present, cancel_feedback=self.player.cancel,
            now=lambda: 0, inspection_seconds=0,
        )

    def received(self, receipt: FeedbackReceipt) -> None:
        self.receipts.append(receipt)
        self.coordinator.receive_feedback(receipt)

    def present(self, cue: ObjectFeedback) -> None:
        self.presented.append(cue)
        line = next(line for line in self.book.lines if line.event == cue.event
                    and not line.moods and not line.periods and not line.weekdays)
        self.presenter.show(cue, Reaction(line.id, line.beats, line.animation,
                                          line.event), self.received)

    def test_named_losses_wait_for_presented_text_before_search_is_ready(self):
        # Geometry and orientation admit these confirmed losses upstream.
        records = []
        for identity in ("dango", "energy_drink", "onigiri"):
            self.memory.update((ObjectObservation(
                identity, identity, "drink" if identity == "energy_drink" else "food",
                100, 0, True, 0,
            ),), now=0)
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
            self.assertEqual(cue.event, "object_place_missing" if expected
                             else "object_search")
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
