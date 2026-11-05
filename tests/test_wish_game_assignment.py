"""Real round admission binds one wish, independently of its eventual outcome."""

import unittest

from support.wishes import INPUTS, coordinator, finish, wish
from support.wishes import WISH_GAME_ASSIGNMENT_WALL as WALL
from support.wishes import wish_game_assignment_pet_with as pet_with

from aiko_pet.games.contracts import GameId, GameRoundEvent
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.moodlets import MoodletId, MoodletOutcome
from aiko_pet.pet.wishes import WishId, WishTargetMode
from tools.pet_test_support import require_test_value


class AssignedGameWishTests(unittest.TestCase):
    def test_specific_next_win_loss_does_not_fall_back_to_play_wish(self):
        free = wish(WishId.PLAY_ANY_GAME)
        concrete = wish(WishId.WIN_ROUND, "blackjack", instance=2)
        pet = pet_with(free, concrete)
        runtime = coordinator(pet)
        start = GameRoundEvent(GameId.BLACKJACK, "actual", 1)
        runtime.observe_round(start, INPUTS)
        finish(runtime, start, "win")  # Aiko loses her assigned next-win attempt.
        self.assertEqual(pet.wishes.active, (free,))
        self.assertFalse(pet.moodlets.active)
        self.assertEqual(pet.friendship, 50)

    def test_assigned_nonloss_failure_cannot_progress_an_easier_play_goal(self):
        free = wish(WishId.PLAY_ANY_GAME)
        strict = wish(WishId.AVOID_ROUND_LOSS, "blackjack", instance=2)
        pet = pet_with(free, strict)
        runtime = coordinator(pet)
        start = GameRoundEvent(GameId.BLACKJACK, "actual", 1)
        runtime.observe_round(start, INPUTS)
        finish(runtime, start, "win")
        self.assertEqual(pet.wishes.active, (free,))
        self.assertEqual(pet.moodlets.active[0].definition_id, MoodletId.DISAPPOINTED)
        cause = pet.moodlets.active[0].causes[0]
        self.assertEqual(require_test_value(cause.wish).instance_id, strict.instance_id)
        self.assertEqual(cause.target_id, "blackjack")

    def test_pin_at_start_is_preserved_even_if_priorities_change_before_result(self):
        exact = wish(WishId.PLAY_GAME, "blackjack")
        free = wish(WishId.PLAY_ANY_GAME, instance=2, pinned=True)
        pet = pet_with(exact, free)
        runtime = coordinator(pet)
        start = GameRoundEvent(GameId.BLACKJACK, "actual", 1)
        runtime.observe_round(start, INPUTS)
        pet.set_wish_pinned(2, False)
        pet.set_wish_pinned(1, True)
        finish(runtime, start, "draw")
        by_id = {w.instance_id: w for w in pet.wishes.active}
        self.assertEqual(by_id[1].game.completed_rounds, 0)
        self.assertEqual(by_id[2].game.completed_rounds, 1)
        self.assertEqual(pet.wishes.refresh_at, 600)

    def test_free_play_accumulates_different_games_sessions_and_reload(self):
        pet = pet_with(wish(WishId.PLAY_ANY_GAME))
        for number, game in enumerate((GameId.CONNECT_FOUR, GameId.MASTERMIND), 1):
            runtime = coordinator(pet)
            event = GameRoundEvent(game, f"actual-{number}", 1)
            runtime.observe_round(event, INPUTS)
            finish(runtime, event, "draw")
            pet = decode_pet_state(encode_pet_state(pet), now=WALL)
        self.assertFalse(pet.wishes.active)
        cause = pet.moodlets.active[0].causes[0]
        self.assertEqual(
            require_test_value(require_test_value(cause.wish).target).mode,
            WishTargetMode.ANY,
        )
        self.assertEqual(require_test_value(cause.wish).target_id, "")
        self.assertEqual(cause.target_id, "mastermind")
        self.assertEqual(require_test_value(cause.game).completed_rounds, 2)
        self.assertEqual(cause.outcome, MoodletOutcome.COMPLETED)

    def test_play_change_excludes_reference_but_accumulates_other_games(self):
        pet = pet_with(wish(WishId.PLAY_OTHER_GAME, "blackjack"))
        runtime = coordinator(pet)
        for number, game in enumerate(
            (GameId.BLACKJACK, GameId.TIC_TAC_TOE, GameId.ROCK_PAPER_SCISSORS), 1
        ):
            start = GameRoundEvent(game, "actual", number)
            runtime.observe_round(start, INPUTS)
            finish(runtime, start, "draw")
            if number == 1:
                self.assertEqual(pet.wishes.active[0].game.completed_rounds, 0)
        self.assertFalse(pet.wishes.active)
        loaded = decode_pet_state(encode_pet_state(pet), now=WALL)
        cause = loaded.moodlets.active[0].causes[0]
        self.assertEqual(require_test_value(cause.wish).target_id, "blackjack")
        self.assertEqual(cause.target_id, "rock_paper_scissors")
        self.assertEqual(require_test_value(cause.game).completed_rounds, 2)

    def test_rematch_accepts_any_result_and_comeback_permits_retries(self):
        for key, outcomes, moodlet in (
            (WishId.REMATCH_GAME, ("draw",), MoodletId.SHARED_PLAY),
            (WishId.COMEBACK_GAME, ("win", "draw", "loss"), MoodletId.PRIDE),
        ):
            with self.subTest(key=key):
                pet = pet_with(wish(key, "blackjack"))
                runtime = coordinator(pet)
                for number, outcome in enumerate(outcomes, 1):
                    start = GameRoundEvent(GameId.BLACKJACK, "actual", number)
                    runtime.observe_round(start, INPUTS)
                    finish(runtime, start, outcome)
                    if number < len(outcomes):
                        self.assertTrue(pet.wishes.active)
                        self.assertFalse(pet.moodlets.active)
                self.assertFalse(pet.wishes.active)
                self.assertEqual(pet.moodlets.active[0].definition_id, moodlet)
                self.assertEqual(pet.friendship, 50)

    def test_dismissed_assignment_cannot_adopt_another_matching_wish(self):
        free = wish(WishId.PLAY_ANY_GAME)
        exact = wish(WishId.PLAY_GAME, "blackjack", instance=2)
        pet = pet_with(free, exact)
        runtime = coordinator(pet)
        start = GameRoundEvent(GameId.BLACKJACK, "actual", 1)
        runtime.observe_round(start, INPUTS)
        pet.dismiss_wish(2)
        finish(runtime, start, "draw")
        self.assertEqual(pet.wishes.active, (free,))
        self.assertFalse(pet.moodlets.active)

    def test_replayed_start_and_result_after_reload_cannot_advance_second_wish(self):
        free = wish(WishId.PLAY_ANY_GAME)
        strict = wish(WishId.WIN_ROUND, "blackjack", instance=2)
        pet = pet_with(free, strict)
        runtime = coordinator(pet)
        start = GameRoundEvent(GameId.BLACKJACK, "actual", 1)
        runtime.observe_round(start, INPUTS)
        finish(runtime, start, "loss")
        pet = decode_pet_state(encode_pet_state(pet), now=WALL)
        checkpoint = pet.capture_checkpoint()
        runtime = coordinator(pet)
        runtime.observe_round(start, INPUTS)
        finish(runtime, start, "loss")
        self.assertEqual(pet.capture_checkpoint(), checkpoint)
        self.assertEqual(pet.wishes.active, (free,))
