"""Pet animation policy classes preserve existing canonical behaviour."""

import unittest

from aiko_pet.pet.animation.animation import FrameClock, SpriteSelection
from aiko_pet.pet.animation.ambient import AmbientDirector
from aiko_pet.pet.animation.priority import (
    AnimationPriority, choose_animation_priority,
)


class PetAnimationPolicyBoundaryTests(unittest.TestCase):
    def test_animation_policies_keep_their_pet_domain_owner(self) -> None:
        self.assertEqual(FrameClock.__module__, "aiko_pet.pet.animation.animation")
        self.assertEqual(SpriteSelection.__module__, "aiko_pet.pet.animation.animation")
        self.assertEqual(AmbientDirector.__module__, "aiko_pet.pet.animation.ambient")


class AnimationPriorityTests(unittest.TestCase):
    def select(
        self, *, game_mode: bool = False, sleeping: bool = False,
        active_action: str | None = None, action_loops: bool = False,
        timed_action_active: bool = False,
    ) -> AnimationPriority:
        return choose_animation_priority(
            game_mode=game_mode, sleeping=sleeping,
            active_action=active_action, action_loops=action_loops,
            timed_action_active=timed_action_active,
        )

    def test_game_action_wins_even_when_sleeping_or_timed(self) -> None:
        self.assertEqual(
            self.select(game_mode=True, sleeping=True,
                        active_action="jumping", timed_action_active=True),
            AnimationPriority("game", animation="jumping"),
        )

    def test_game_waiting_clears_looping_or_absent_action(self) -> None:
        self.assertEqual(
            self.select(game_mode=True, active_action="idle",
                        action_loops=True),
            AnimationPriority("game", animation="waiting", clear_action=True),
        )

    def test_sleep_clears_action_and_interrupts_walk(self) -> None:
        self.assertEqual(
            self.select(sleeping=True, active_action="waving"),
            AnimationPriority(
                "sleep", animation="sleep",
                clear_action=True, interrupt_walk=True,
            ),
        )

    def test_one_shot_action_overrides_timed_action(self) -> None:
        self.assertEqual(
            self.select(active_action="eat", timed_action_active=True),
            AnimationPriority("action", animation="eat"),
        )

    def test_timed_action_only_when_no_foreground_action(self) -> None:
        self.assertEqual(
            self.select(active_action="idle", action_loops=True,
                        timed_action_active=True),
            AnimationPriority("timed"),
        )

    def test_passive_clears_stale_action_without_interrupting_walk(self) -> None:
        self.assertEqual(
            self.select(active_action="idle", action_loops=True),
            AnimationPriority("passive", clear_action=True),
        )
