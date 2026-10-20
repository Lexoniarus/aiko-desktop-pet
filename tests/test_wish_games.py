"""Round evidence resolves fixed objectives, with bounded restart-safe progress."""

import unittest
from dataclasses import replace

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.game_experience import GameExperienceCoordinator
from aiko_pet.games.contracts import GameId, GameRoundEvent
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.moodlets import MoodletId
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState

WALL = 1800000000.0


def wish_state(key, target="blackjack", instance=1):
    return WishState(
        instance + 1,
        (ActiveWish(instance, key, target, 0, 14400),),
        ((WishArea.GAMES, 0),),
    )


def pet_with(key):
    return PetState(
        updated_at=WALL, lived_seconds=100, friendship=50, wishes=wish_state(key)
    )


def complete(pet, outcome, number=1, session="a", game="blackjack", **kwargs):
    args = dict(
        instance_id=1,
        game_id=game,
        session_id=session,
        round_id=f"{session}:{number}",
        started_at=50,
        outcome=outcome,
    )
    args.update(kwargs)
    pet.complete_wish_round(**args)


class GameWishTests(unittest.TestCase):
    def test_retryable_round_win_keeps_only_bounded_progress_across_losses(self):
        pet = pet_with(WishId.WIN_ROUND)
        for number in range(1, 6):
            complete(pet, "loss", number)
            self.assertEqual(len(pet.wishes.active[0].game.round_ids), 1)
            self.assertFalse(pet.moodlets.active)
        complete(pet, "draw", 1, "b")
        complete(pet, "win", 2, "b")
        self.assertFalse(pet.wishes.active)
        self.assertEqual(pet.moodlets.active[0].definition_id, MoodletId.PRIDE)
        self.assertEqual(pet.moodlets.active[0].level, 1)
        before = pet.capture_checkpoint()
        complete(pet, "win", 2, "b")
        self.assertEqual(pet.capture_checkpoint(), before)

    def test_next_round_goal_resolves_once_and_loss_is_neutral(self):
        for outcome in ("win", "draw", "loss"):
            pet = pet_with(WishId.AVOID_ROUND_LOSS)
            complete(pet, outcome)
            self.assertFalse(pet.wishes.active)
            self.assertEqual(bool(pet.moodlets.active), outcome != "loss")
            self.assertEqual(pet.friendship, 50 if outcome == "loss" else 50.25)
            before = pet.capture_checkpoint()
            complete(pet, "win", 2)
            self.assertEqual(pet.capture_checkpoint(), before)

    def test_fixed_block_waits_for_three_rounds_across_sessions_and_reload(self):
        pet = pet_with(WishId.WIN_OVERALL)
        complete(pet, "win")
        complete(pet, "loss", 2)
        self.assertEqual(pet.wishes.active[0].game.wins, 1)
        self.assertFalse(pet.moodlets.active)
        pet = decode_pet_state(encode_pet_state(pet), now=WALL)
        complete(pet, "win", 1, "new-session")
        self.assertFalse(pet.wishes.active)
        self.assertEqual(pet.moodlets.active[0].level, 2)
        self.assertEqual(pet.moodlets.active[0].remaining_seconds, 7200)
        self.assertEqual(pet.friendship, 50.25)

    def test_all_draws_relieve_nonloss_but_do_not_win_overall(self):
        for key in (WishId.AVOID_OVERALL_LOSS, WishId.WIN_OVERALL):
            pet = pet_with(key)
            for number in range(1, 4):
                complete(pet, "draw", number)
                if number < 3:
                    self.assertTrue(pet.wishes.active)
            self.assertFalse(pet.wishes.active)
            self.assertEqual(
                bool(pet.moodlets.active), key == WishId.AVOID_OVERALL_LOSS
            )

    def test_shared_play_requires_two_in_one_session_and_rejects_duplicate_rounds(self):
        pet = pet_with(WishId.PLAY_GAME)
        complete(pet, "win")
        complete(pet, "win")
        self.assertEqual(len(pet.wishes.active[0].game.round_ids), 1)
        complete(pet, "loss", 1, "b")
        self.assertEqual(pet.wishes.active[0].game.round_ids, ("b:1",))
        complete(pet, "draw", 2, "b")
        self.assertFalse(pet.wishes.active)
        self.assertEqual(pet.moodlets.active[0].definition_id, MoodletId.SHARED_PLAY)

    def test_wrong_game_missing_identity_old_start_and_deadline_cannot_fulfill(self):
        for game, instance, started in (
            ("tic_tac_toe", 1, 50),
            ("blackjack", 99, 50),
            ("blackjack", 1, -1),
        ):
            pet = pet_with(WishId.WIN_ROUND)
            before = pet.capture_checkpoint()
            complete(pet, "win", game=game, instance_id=instance, started_at=started)
            self.assertEqual(pet.capture_checkpoint(), before)
        pet = pet_with(WishId.WIN_ROUND)
        pet.restore_checkpoint(replace(pet.capture_checkpoint(), lived_seconds=14400))
        complete(pet, "win")
        self.assertTrue(pet.wishes.active)
        self.assertFalse(pet.moodlets.active)

    def test_application_captures_existing_wish_and_translates_each_game_once(self):
        for game in GameId:
            pet = pet_with(WishId.WIN_ROUND)
            pet.restore_checkpoint(
                replace(
                    pet.capture_checkpoint(),
                    wishes=wish_state(WishId.WIN_ROUND, game.value),
                )
            )
            coordinator = GameExperienceCoordinator(
                pet,
                make_aiko_mind(started_at=0),
                AdaptiveRoutine(),
                clock=ActiveSessionClock(lambda: 0),
            )
            inputs = SessionInputs(WALL, 0, False, None, False, False, None)
            start = GameRoundEvent(game, "actual", 1)
            finish = replace(start, outcome="loss")  # Player loss = Aiko victory.
            coordinator.observe_round(finish, inputs)
            self.assertTrue(pet.wishes.active)
            coordinator.observe_round(start, inputs)
            coordinator.observe_round(finish, inputs)
            before = pet.capture_checkpoint()
            coordinator.observe_round(finish, inputs)
            self.assertEqual(pet.capture_checkpoint(), before)
            self.assertFalse(pet.wishes.active)
            self.assertEqual(pet.friendship, 50.25)
            self.assertEqual(
                pet.fun, 75
            )  # Ordinary session effects still wait for close.
            coordinator.complete(GameExperience(game.value, 2, 1, 0, 1), inputs)
            self.assertLessEqual(
                sum(e.amount for e in pet.friendship_history.rewards), 0.75
            )

    def test_round_already_underway_does_not_adopt_a_later_wish(self):
        pet = PetState(updated_at=WALL, lived_seconds=100)
        coordinator = GameExperienceCoordinator(
            pet,
            make_aiko_mind(started_at=0),
            AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: 0),
        )
        inputs = SessionInputs(WALL, 0, False, None, False, False, None)
        start = GameRoundEvent(GameId.BLACKJACK, "early", 1)
        coordinator.observe_round(start, inputs)
        pet.restore_checkpoint(
            replace(pet.capture_checkpoint(), wishes=wish_state(WishId.WIN_ROUND))
        )
        coordinator.observe_round(replace(start, outcome="loss"), inputs)
        self.assertTrue(pet.wishes.active)
        self.assertFalse(pet.moodlets.active)
