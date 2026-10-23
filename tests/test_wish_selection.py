"""Deterministic wish pools, authored weights and actual round prerequisites."""

import random
import unittest
from dataclasses import replace

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.game_experience import GameExperienceCoordinator
from aiko_pet.games.contracts import GameId, GameRoundEvent
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.care_evidence import (
    MAX_CARE_EXPERIENCES,
    CareActivity,
    CareExperience,
)
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.moodlets import MoodletOutcome
from aiko_pet.pet.needs import NeedLevels
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wish_selection import replenish_wishes, wish_area_weight
from aiko_pet.pet.wishes import (
    ActiveWish,
    WishArea,
    WishContext,
    WishId,
    WishState,
    WishTargetKind,
    WishTargetMode,
)

DEFINITIONS = WISH_CATALOG.definitions
FULL = NeedLevels(100, 100, 100, 100, 100)


class SelectionRandom(random.Random):
    """Record the actual weighted draws without sampling noisy percentages."""

    def __init__(self, seed=4):
        super().__init__(seed)
        self.draws = []

    def choices(self, population, weights=None, *, cum_weights=None, k=1):
        self.draws.append((tuple(population), tuple(weights)))
        return super().choices(population, weights, cum_weights=cum_weights, k=k)


def pick(*keys, context=WishContext(), needs=FULL, elapsed=100, state=WishState(),
         rng=None):
    return replenish_wishes(
        state, elapsed=elapsed, sleeping=False, context=context, needs=needs,
        definitions={k: DEFINITIONS[k] for k in keys} if keys else DEFINITIONS,
        rng=rng if rng is not None else random.Random(7),
    )


def played(outcome=MoodletOutcome.LOSS, game="blackjack", at=100):
    return CareExperience("round:1", at, CareActivity.PLAY, outcome,
                          WishArea.GAMES, WishTargetKind.GAME, game)


class WishSelectionTests(unittest.TestCase):
    def test_need_bands_use_exact_boundaries_for_every_area(self):
        for value, weight in ((100, 1), (70.01, 1), (70, 3), (40.01, 3),
                              (40, 5), (25.01, 5), (25, 7), (0, 7)):
            for area in WishArea:
                with self.subTest(value=value, area=area):
                    self.assertEqual(wish_area_weight(
                        area, NeedLevels(value, value, value, value, value),
                    ), weight)

    def test_area_draw_precedes_form_draw_without_counting_targets_as_weight(self):
        rng = SelectionRandom()
        pick(context=WishContext(online_social=True),
             needs=NeedLevels(20, 100, 80, 50, 30), rng=rng)
        areas, weights = rng.draws[0]
        self.assertEqual(dict(zip(areas, weights)), {
            WishArea.FOOD: 7, WishArea.GAMES: 1, WishArea.SOCIAL: 3,
            WishArea.AFFECTION: 5,
        })
        forms, _ = rng.draws[1]
        self.assertEqual(len({c.definition.area for c in forms}), 1)

    def test_full_food_and_affection_do_not_exclude_personal_wishes(self):
        for key in (WishId.FOOD, WishId.PET):
            with self.subTest(key=key):
                state = pick(key, context=WishContext(petting_welcome=False))
                self.assertTrue(state.active)
                self.assertTrue(all(w.definition_id == key for w in state.active))
        for context in (WishContext(petting_refused=True), WishContext(crowded=True)):
            self.assertFalse(pick(WishId.PET, context=context).active)

    def test_full_fun_social_can_fill_all_slots_without_food_or_affection(self):
        for keys in ((WishId.PLAY_GAME,),
                     (WishId.SOCIAL_ANY, WishId.CHAT, WishId.FACT)):
            with self.subTest(keys=keys):
                state = pick(*keys, context=WishContext(online_social=True))
                self.assertEqual(len(state.active), 3)
                signatures = {(w.goal_snapshot, w.target) for w in state.active}
                self.assertEqual(len(signatures), 3)
                pet = PetState(lived_seconds=100, wishes=state)
                loaded = decode_pet_state(encode_pet_state(pet), now=1800000000)
                self.assertEqual(loaded.wishes, state)

    def test_existing_food_affection_survive_rising_to_full_needs(self):
        low = pick(WishId.FOOD, WishId.PET,
                   needs=NeedLevels(20, 100, 100, 100, 20))
        self.assertEqual(pick(WishId.FOOD, WishId.PET, state=low,
                              elapsed=101, needs=FULL), low)

    def test_exact_semantic_duplicate_cannot_fill_another_slot(self):
        definition = replace(DEFINITIONS[WishId.PLAY_GAME], targets=("blackjack",))
        state = replenish_wishes(
            WishState(), elapsed=100, sleeping=False, needs=FULL,
            context=WishContext(), definitions={definition.id: definition},
            rng=random.Random(1),
        )
        self.assertEqual(len(state.active), 1)

    def test_catalogue_weights_reach_the_actual_form_draw(self):
        examples = (
            ((WishId.FOOD, WishId.AVOID_FOOD),
             WishContext(repetitive_food="apple"), {WishId.FOOD: 70,
                                                   WishId.AVOID_FOOD: 30}),
            ((WishId.SOCIAL_ANY, WishId.CHAT, WishId.SINGLE, WishId.TWO_PARTS,
              WishId.FACT), WishContext(online_social=True), {
                  WishId.SOCIAL_ANY: 30, WishId.CHAT: 25, WishId.SINGLE: 15,
                  WishId.TWO_PARTS: 15, WishId.FACT: 15,
              }),
            ((WishId.PLAY_ANY_GAME, WishId.PLAY_GAME, WishId.WIN_ROUND,
              WishId.AVOID_ROUND_LOSS, WishId.WIN_OVERALL, WishId.AVOID_OVERALL_LOSS),
             WishContext(), {WishId.PLAY_ANY_GAME: 30, WishId.PLAY_GAME: 30,
                             WishId.WIN_ROUND: 10, WishId.AVOID_ROUND_LOSS: 15,
                             WishId.WIN_OVERALL: 10, WishId.AVOID_OVERALL_LOSS: 5}),
        )
        for keys, context, expected in examples:
            with self.subTest(keys=keys):
                rng = SelectionRandom()
                pick(*keys, context=context, rng=rng)
                forms, weights = rng.draws[1]
                self.assertEqual({c.definition.id: w for c, w in zip(forms, weights)},
                                 expected)

    def test_food_variety_requires_real_reference_and_has_no_duplicate_form(self):
        self.assertFalse(pick(WishId.AVOID_FOOD).active)
        state = pick(WishId.AVOID_FOOD,
                     context=WishContext(repetitive_food="apple"))
        self.assertEqual(len(state.active), 1)
        self.assertEqual(state.active[0].target.mode, WishTargetMode.EXCLUDE)
        self.assertEqual(state.active[0].target_id, "apple")

    def test_online_capability_gates_specific_forms_but_not_free_choice_chat(self):
        state = pick(WishId.SOCIAL_ANY, WishId.CHAT, WishId.SINGLE,
                     WishId.TWO_PARTS, WishId.FACT)
        self.assertEqual({w.definition_id for w in state.active},
                         {WishId.SOCIAL_ANY, WishId.CHAT})
        state = pick(WishId.PLAY_GAME, context=WishContext(games_ready=False))
        self.assertEqual(len(state.active), 3)

    def test_experience_window_is_half_open_and_does_not_infer_missing_history(self):
        keys = (WishId.PLAY_OTHER_GAME, WishId.REMATCH_GAME, WishId.COMEBACK_GAME)
        self.assertFalse(pick(*keys).active)
        for elapsed, eligible in ((99, False), (100, True), (1899.99, True),
                                  (1900, False)):
            with self.subTest(elapsed=elapsed):
                state = pick(*keys, elapsed=elapsed,
                             context=WishContext(recent_play=played()))
                self.assertEqual(bool(state.active), eligible)

    def test_experience_multiplier_applies_once_and_rematches_are_alternatives(self):
        rng = SelectionRandom()
        state = pick(WishId.PLAY_OTHER_GAME, WishId.REMATCH_GAME,
                     WishId.COMEBACK_GAME, context=WishContext(recent_play=played()),
                     rng=rng)
        forms, weights = rng.draws[1]
        self.assertEqual({c.definition.id: w for c, w in zip(forms, weights)}, {
            WishId.PLAY_OTHER_GAME: 15, WishId.REMATCH_GAME: 15,
            WishId.COMEBACK_GAME: 7.5,
        })
        self.assertEqual(len(state.active), 2)
        self.assertEqual(sum(w.definition_id in (WishId.REMATCH_GAME,
                                                 WishId.COMEBACK_GAME)
                             for w in state.active), 1)
        self.assertTrue(all(w.target_id == "blackjack" for w in state.active))
        other = next(w for w in state.active
                     if w.definition_id == WishId.PLAY_OTHER_GAME)
        self.assertEqual(other.target.mode, WishTargetMode.EXCLUDE)

    def test_later_nonloss_replaces_defeat_fact_and_pinned_goal_keeps_reference(self):
        keys = (WishId.REMATCH_GAME, WishId.COMEBACK_GAME)
        for outcome in (MoodletOutcome.WIN, MoodletOutcome.DRAW):
            self.assertFalse(pick(*keys, context=WishContext(
                recent_play=played(outcome),
            )).active)
        original = pick(WishId.REMATCH_GAME,
                        context=WishContext(recent_play=played()))
        pinned = replace(original, active=tuple(replace(w, pinned=True)
                                               for w in original.active))
        later = pick(*keys, state=pinned, elapsed=3000,
                     context=WishContext(recent_play=played(MoodletOutcome.WIN,
                                                           "mastermind", 3000)))
        self.assertEqual(later.active, pinned.active)

    def test_actual_round_fact_persists_without_wish_or_immediate_reward(self):
        wall = 1800000000
        pet = PetState(updated_at=wall, lived_seconds=100)
        coordinator = GameExperienceCoordinator(
            pet, make_aiko_mind(started_at=0), AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: 0),
        )
        inputs = SessionInputs(wall, 0, False, None, False, False, None)
        start = GameRoundEvent(GameId.BLACKJACK, "actual", 1)
        finish = replace(start, outcome="win")  # Player wins, Aiko loses.
        before = pet.capture_checkpoint()
        coordinator.observe_round(finish, inputs)
        self.assertEqual(pet.capture_checkpoint(), before)
        coordinator.observe_round(start, inputs)
        self.assertIsNone(pet.moodlets.care_evidence)
        coordinator.observe_round(finish, inputs)
        evidence = pet.moodlets.care_evidence
        self.assertEqual(len(evidence.experiences), 1)
        self.assertEqual(evidence.experiences[0].outcome, MoodletOutcome.LOSS)
        self.assertFalse(evidence.experiences[0].pleasant)
        self.assertFalse(evidence.encounters)
        self.assertFalse(pet.moodlets.active)
        self.assertEqual((pet.friendship, pet.fun), (before.friendship, before.fun))
        checkpoint = pet.capture_checkpoint()
        coordinator.observe_round(finish, inputs)
        self.assertEqual(pet.capture_checkpoint(), checkpoint)
        loaded = decode_pet_state(encode_pet_state(pet), now=wall)
        self.assertEqual(loaded.moodlets.care_evidence, evidence)
        # The aggregate derives eligibility from its saved latest actual round.
        expected = {WishId.PLAY_OTHER_GAME, WishId.REMATCH_GAME}
        rng = SelectionRandom()
        loaded.evaluate_wishes(WishContext(), rng=rng)
        forms = [c.definition.id for pop, _ in rng.draws
                 for c in pop if hasattr(c, "definition")]
        self.assertTrue(expected.issubset(forms))

    def test_pinned_target_prevents_duplicate_without_blocking_other_games(self):
        definition = DEFINITIONS[WishId.PLAY_GAME]
        pinned = ActiveWish(1, definition.id, "blackjack", 0, 600,
                            goal=definition.goal, pinned=True,
                            target=definition.bind_target("blackjack"))
        state = pick(WishId.PLAY_GAME, elapsed=600, state=WishState(
            2, (pinned,), ((WishArea.GAMES, 0),), refresh_at=600,
        ))
        self.assertEqual(state.active[0], pinned)
        self.assertEqual(len({w.target for w in state.active}), 3)

    def test_bounded_round_evidence_keeps_latest_result_across_save(self):
        pet = PetState(lived_seconds=100)
        for index in range(MAX_CARE_EXPERIENCES + 2):
            pet.record_completed_game_round(
                game_id="blackjack", round_id=f"actual:{index}", outcome="loss",
            )
        pet.record_completed_game_round(
            game_id="blackjack", round_id="later:1", outcome="win",
        )
        checkpoint = pet.capture_checkpoint()
        pet.record_completed_game_round(
            game_id="blackjack", round_id="later:1", outcome="win",
        )
        self.assertEqual(pet.capture_checkpoint(), checkpoint)
        loaded = decode_pet_state(encode_pet_state(pet), now=1800000000)
        evidence = loaded.moodlets.care_evidence
        self.assertEqual(len(evidence.experiences), MAX_CARE_EXPERIENCES)
        self.assertEqual(evidence.experiences[-1].outcome, MoodletOutcome.WIN)
        rng = SelectionRandom()
        loaded.evaluate_wishes(WishContext(), rng=rng)
        forms = {c.definition.id for pop, _ in rng.draws
                 for c in pop if hasattr(c, "definition")}
        self.assertNotIn(WishId.REMATCH_GAME, forms)
        self.assertNotIn(WishId.COMEBACK_GAME, forms)
