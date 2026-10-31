"""Desktop pointer bridge preserves sampling and event dispatch."""

import unittest
from unittest.mock import Mock

from aiko_pet.application.cursor_behaviour import CursorBehaviourCoordinator
from aiko_pet.application.cursor_observation import CursorObservation
from aiko_pet.application.settings import PetSettings
from aiko_pet.desktop.pointer_runtime import PointerRuntime, PointerRuntimePorts
from aiko_pet.pet.interaction_events import CursorWarningReceipt
from aiko_pet.pet.mind.cursor_attention import CursorAttention, CursorPerception
from aiko_pet.pet.mind.cursor_behaviour import CursorBehaviourPolicy
from aiko_pet.pet.state import PetState
from tools.pet_test_support import set_test_pet_values


class PointerRuntimeTests(unittest.TestCase):
    def test_display_receipt_cannot_tick_policy_or_mutate_pet(self):
        observer = CursorObservation(CursorAttention())
        pet = PetState()
        set_test_pet_values(pet, mood=20)
        policy = CursorBehaviourPolicy(session_id="bridge")
        coordinator = CursorBehaviourCoordinator(pet, PetSettings(), observer, policy)
        experiences = []
        warnings = []

        def display(event, now):
            warnings.append(event)
            before = pet.capture_checkpoint()
            score = policy.attention
            receipt = CursorWarningReceipt(event.warning_id, now + .01, True)
            self.assertEqual(pet.capture_checkpoint(), before)
            self.assertEqual(policy.attention, score)
            return receipt

        runtime = PointerRuntime(observer, PointerRuntimePorts(
            sample=lambda: (400, 100, 1000), game_mode=lambda: False,
            eyes=lambda: (196, 82), on_motion=lambda *_args: None,
            on_warning=display, on_experience=experiences.append,
        ), coordinator)
        checkpoint = pet.capture_checkpoint()
        for at, closing in ((10, 2), (10, 2), (10.1, -2)):
            observer.current = CursorPerception(
                sampled_at=at, pointer=(400, 100), distance=.5, speed=4,
                closing_speed=closing, side=1, valid=True,
            )
            runtime.begin_behaviour(at)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].tone, "cautious")
        self.assertFalse(experiences)
        self.assertEqual(pet.capture_checkpoint(), checkpoint)
        observer.current = CursorPerception(
            sampled_at=10.2, pointer=(400, 100), distance=.5, speed=4,
            closing_speed=2, side=1, valid=True,
        )
        runtime.begin_behaviour(10.2)
        self.assertEqual([e.feeling for e in experiences], ["fear"])
        self.assertEqual(len(pet.moodlets.active), 1)
        runtime.begin_behaviour(10.2)
        self.assertEqual(len(experiences), 1)

    def test_events_are_sent_only_for_changed_pointer(self) -> None:
        attention = CursorAttention()
        on_motion = Mock()
        samples = iter(((10, 20, 1920), (1000, 20, 1920)))
        runtime = PointerRuntime(
            CursorObservation(attention),
            PointerRuntimePorts(
                sample=lambda: next(samples),
                game_mode=lambda: False,
                eyes=lambda: (100, 20),
                on_motion=on_motion,
            ),
        )
        self.assertEqual(runtime.observe(100.0), (10, 20))
        on_motion.assert_not_called()
        self.assertEqual(runtime.observe(101.0), (1000, 20))
        on_motion.assert_called_once_with(900.0, 1920, 101.0)
        self.assertEqual(attention.last_pointer_move, 101.0)
