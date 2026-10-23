"""Round evidence resolves fixed objectives, with bounded restart-safe progress."""

import unittest
from dataclasses import replace
from itertools import product

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.game_experience import GameExperienceCoordinator
from aiko_pet.games.contracts import GameId, GameRoundEvent
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import (
    MoodletAttribution,
    MoodletId,
    MoodletOutcome,
    advance_moodlets,
)
from aiko_pet.pet.needs import NeedLevels
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState

WALL = 1800000000.0


def wish_state(key, target="blackjack", instance=1, current=False):
    return WishState(
        instance + 1,
        (ActiveWish(instance, key, target, 0, 14400,
                    goal=WISH_CATALOG.definitions[key].goal if current else None),),
        ((WishArea.GAMES, 0),),
    )


def pet_with(key, current=False):
    return PetState(
        updated_at=WALL, lived_seconds=100, friendship=50,
        wishes=wish_state(key, current=current),
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
    def test_new_total_wins_survive_losses_draws_sessions_and_reload(self):
        pet = pet_with(WishId.WIN_OVERALL, current=True)
        for number, outcome in enumerate(("win", "loss", "win", "draw", "win"), 1):
            complete(pet, outcome, number, f"session-{number}")
            if number < 5:
                self.assertTrue(pet.wishes.active)
                checkpoint = pet.capture_checkpoint()
                complete(pet, outcome, number, f"session-{number}")
                self.assertEqual(pet.capture_checkpoint(), checkpoint)
            pet = decode_pet_state(encode_pet_state(pet), now=WALL)
        self.assertFalse(pet.wishes.active)
        episode = pet.moodlets.active[0]
        self.assertEqual((episode.definition_id, episode.level), (MoodletId.PRIDE, 2))
        self.assertEqual(len(episode.causes), 1)
        cause = episode.causes[0]
        self.assertEqual(cause.event_id, "session-5:5")
        assert cause.wish is not None and cause.game is not None
        self.assertEqual(cause.wish.objective, "total_wins")
        self.assertEqual((cause.game.completed_rounds, cause.game.wins,
                          cause.game.losses), (5, 3, 1))

    def test_new_total_play_accumulates_across_sessions_without_requiring_a_win(self):
        pet = pet_with(WishId.PLAY_GAME, current=True)
        complete(pet, "loss", 1, "first")
        pet = decode_pet_state(encode_pet_state(pet), now=WALL)
        complete(pet, "draw", 1, "second")
        self.assertFalse(pet.wishes.active)
        cause = pet.moodlets.active[0].causes[0]
        self.assertEqual(cause.outcome, MoodletOutcome.COMPLETED)
        assert cause.game is not None
        self.assertEqual(cause.game.round_outcome, MoodletOutcome.DRAW)
        self.assertEqual(cause.game.completed_rounds, 2)

    def test_next_win_resolves_on_its_first_result_without_retry_or_loss_moodlet(self):
        for outcome in ("win", "loss", "draw"):
            with self.subTest(outcome=outcome):
                pet = pet_with(WishId.WIN_ROUND, current=True)
                complete(pet, outcome)
                self.assertFalse(pet.wishes.active)
                self.assertEqual(bool(pet.moodlets.active), outcome == "win")
                before = pet.capture_checkpoint()
                complete(pet, "win", 2)
                self.assertEqual(pet.capture_checkpoint(), before)

    def test_failed_nonloss_wishes_stack_once_keep_three_causes_and_decay(self):
        pet = pet_with(WishId.AVOID_ROUND_LOSS, current=True)
        for instance in range(1, 5):
            pet.restore_checkpoint(replace(pet.capture_checkpoint(), wishes=wish_state(
                WishId.AVOID_ROUND_LOSS, instance=instance, current=True,
            )))
            complete(pet, "loss", instance_id=instance)
            episode = pet.moodlets.active[0]
            self.assertEqual(episode.definition_id, MoodletId.DISAPPOINTED)
            self.assertEqual((episode.level, episode.remaining_seconds),
                             (min(instance, 3), 1800))
            self.assertEqual(episode.attribution, MoodletAttribution.UNKNOWN)
            self.assertEqual(pet.friendship, 50)
            pet = decode_pet_state(encode_pet_state(pet), now=WALL)
            before = pet.capture_checkpoint()
            complete(pet, "loss", instance_id=instance)
            self.assertEqual(pet.capture_checkpoint(), before)
        causes = pet.moodlets.active[0].causes
        self.assertEqual([c.wish.instance_id for c in causes if c.wish], [2, 3, 4])
        healthy = NeedLevels(80, 80, 80, 80, 80)
        for seconds, expected in ((1800, 2), (3600, 1), (5400, 0)):
            aged = advance_moodlets(pet.moodlets, seconds, elapsed=100,
                                    before=healthy, after=healthy,
                                    definitions=MOODLET_CATALOG.definitions)
            self.assertEqual(aged.active[0].level if aged.active else 0, expected)
            if aged.active:
                self.assertEqual(aged.active[0].causes, causes[-expected:])
        pet.restore_checkpoint(replace(pet.capture_checkpoint(), wishes=wish_state(
            WishId.WIN_ROUND, instance=5, current=True,
        )))
        complete(pet, "win", instance_id=5)
        self.assertEqual({e.definition_id for e in pet.moodlets.active},
                         {MoodletId.DISAPPOINTED, MoodletId.PRIDE})

    def test_block_defeat_records_overall_loss_even_when_final_round_is_a_draw(self):
        pet = pet_with(WishId.AVOID_OVERALL_LOSS, current=True)
        for number, outcome in enumerate(("loss", "loss", "draw"), 1):
            complete(pet, outcome, number)
        cause = pet.moodlets.active[0].causes[0]
        self.assertEqual(cause.outcome, MoodletOutcome.LOSS)
        assert cause.game is not None
        self.assertEqual(cause.game.round_outcome, MoodletOutcome.DRAW)
        self.assertEqual(cause.game.losses, 2)
        self.assertEqual(pet.friendship, 50)

    def test_cumulative_attempts_keep_bounded_receipts_and_exact_counts(self):
        pet = pet_with(WishId.WIN_OVERALL, current=True)
        for number in range(1, 151):
            complete(pet, "loss", number)
        progress = pet.wishes.active[0].game
        self.assertEqual((len(progress.round_ids), progress.completed_rounds,
                          progress.losses), (100, 150, 150))
        pet = decode_pet_state(encode_pet_state(pet), now=WALL)
        before = pet.capture_checkpoint()
        complete(pet, "loss", 150)
        self.assertEqual(pet.capture_checkpoint(), before)
        for number in range(151, 154):
            complete(pet, "win", number)
        self.assertFalse(pet.wishes.active)
        assert pet.moodlets.active[0].causes[0].game is not None
        self.assertEqual(pet.moodlets.active[0].causes[0].game.completed_rounds, 153)

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

    def test_next_nonloss_resolves_once_with_no_direct_relationship_loss(self):
        for outcome, pinned in product(("win", "draw", "loss"), (False, True)):
            pet = pet_with(WishId.AVOID_ROUND_LOSS)
            if pinned:
                pet.restore_checkpoint(replace(
                    pet.capture_checkpoint(), lived_seconds=20000,
                    wishes=replace(pet.wishes, active=(
                        replace(pet.wishes.active[0], pinned=True),
                    )),
                ))
            complete(pet, outcome)
            self.assertFalse(pet.wishes.active)
            self.assertEqual(pet.moodlets.active[0].definition_id,
                             MoodletId.DISAPPOINTED if outcome == "loss"
                             else MoodletId.RELIEF)
            self.assertEqual(pet.friendship, 50)
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
        self.assertEqual(pet.moodlets.active[0].remaining_seconds, 2700)
        self.assertEqual(pet.friendship, 50)

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
            with self.subTest(game=game):
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
                self.assertEqual(pet.friendship, 50)
                # Ordinary session effects still wait for close.
                self.assertEqual(pet.fun, 75)
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
