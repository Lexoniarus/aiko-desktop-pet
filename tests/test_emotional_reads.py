"""Passive snapshots expose the full emotional model without running transitions."""

import unittest
from dataclasses import FrozenInstanceError, replace

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.pet.emotions import EmotionalState
from aiko_pet.pet.friendship_history import FriendshipHistory
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import (
    MoodletAttribution,
    MoodletCause,
    MoodletCauseKind,
    MoodletEpisode,
    MoodletGameResult,
    MoodletId,
    MoodletOutcome,
    MoodletState,
    MoodletWishCause,
)
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import (
    ActiveWish,
    GameWishProgress,
    WishContext,
    WishGoal,
    WishId,
    WishObjective,
    WishRestriction,
    WishState,
)
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.view_models.emotional_text import (
    MOODLET_ICONS,
    moodlet_description,
    wish_progress,
)
from aiko_pet.ui.view_models.moodlet_causes import cause_description
from aiko_pet.ui.view_models.projections import project_hover, project_status
from tools.pet_test_support import set_test_pet_values


class EmotionalReadTests(unittest.TestCase):
    def test_all_tiers_show_only_real_causes_and_the_original_goal(self):
        causes = tuple(MoodletCause(
            MoodletCauseKind.WISH_FULFILLED, i, f"round:{i}",
            wish=MoodletWishCause(i, "win_overall", game, "total_wins", 3),
            target_id=game, outcome=MoodletOutcome.WIN,
            game=MoodletGameResult(MoodletOutcome.DRAW, 7, 3, 2), level=i,
        ) for i, game in enumerate(("blackjack", "tic_tac_toe",
                                   "rock_paper_scissors"), 1))
        for level, receipts in ((1, causes), (2, causes[:1]), (3, causes)):
            pet = PetState(moodlets=MoodletState(active=(MoodletEpisode(
                1, MoodletId.PRIDE, level, 0, 3, 100, causes=receipts,
            ),)))
            before = pet.capture_checkpoint()
            view = project_hover(snapshot_pet(pet), context_at(1800000000),
                                 ComputerSnapshot(), observe_computer=False)
            text = moodlet_description(view.emotional.moodlets[0])
            self.assertEqual(text.count("Wunsch erfüllt"), len(receipts))
            self.assertIn("Blackjack", text)
            self.assertIn("Ursprüngliche Zielmenge: 3", text)
            self.assertIn("Letzte Runde: unentschieden", text)
            self.assertIn("Ergebnis des Wunsches/Erlebnisses: gewonnen", text)
            self.assertEqual(pet.capture_checkpoint(), before)

    def test_food_cause_distinguishes_avoided_target_from_actual_handover(self):
        cause = MoodletCause(
            MoodletCauseKind.WISH_FULFILLED, 1, "offer:1",
            wish=MoodletWishCause(1, "avoid_food", "donut", "food_handover", 0),
            target_id="apple", outcome=MoodletOutcome.HANDOVER,
        )
        text = cause_description(cause)
        self.assertIn("Donut", text)
        self.assertIn("Tatsächlich: Apfel", text)
        self.assertIn("übergeben", text)
        legacy = cause_description(MoodletCause(MoodletCauseKind.LEGACY, 0))
        self.assertIn("nicht gespeichert", legacy)
        self.assertNotIn("mit dir", legacy)

    def test_status_uses_real_target_sleep_reason_stage_and_known_contact(self):
        state = PetState(
            satiety=100,
            energy=100,
            fun=100,
            social=100,
            affection=100,
            mood=53,
            friendship=0,
            sleeping=True,
            sleep_origin="manual",
            lived_seconds=1800,
            relationship=FriendshipHistory(last_contact=600),
        )
        before = state.capture_checkpoint()
        read = snapshot_pet(state)
        self.assertEqual(read.mood_target, 80)
        self.assertEqual(read.mood, 53)
        self.assertEqual(read.contact_absence_seconds, 1200)
        view = project_status(
            read,
            context_at(1_800_000_000),
            None,
            ComputerSnapshot(),
            observe_computer=False,
        )
        self.assertIn("80 / 100", view.wellbeing_line)
        self.assertIn("Bekanntschaft", view.relationship_line)
        self.assertEqual(view.sleep_context_line, "Manuell schlafen gelegt.")
        self.assertIn("20 Min.", view.contact_line)
        self.assertEqual(state.capture_checkpoint(), before)

    def test_all_families_reach_both_views_with_full_composition_and_localized_copy(
        self,
    ):
        episodes = tuple(
            MoodletEpisode(i, key, 1, 0, 0, 7200)
            for i, key in enumerate(MOODLET_CATALOG.definitions, 1)
        )
        state = PetState(moodlets=MoodletState(active=episodes))
        before = state.capture_checkpoint()
        read = snapshot_pet(state)
        time = context_at(1_800_000_000)
        hover = project_hover(read, time, ComputerSnapshot(), observe_computer=False)
        status = project_status(
            read, time, None, ComputerSnapshot(), observe_computer=False
        )
        self.assertEqual(hover.emotional, status.emotional)
        self.assertEqual(len(status.emotional.moodlets), 19)
        self.assertEqual(len(read.emotions.influences), 19)
        self.assertTrue(set(MoodletId) <= set(MOODLET_ICONS))
        self.assertEqual(
            {m.value.definition_id for m in status.emotional.moodlets}, set(MoodletId)
        )
        self.assertTrue(
            all(m.label and m.description for m in status.emotional.moodlets)
        )
        self.assertEqual(state.capture_checkpoint(), before)

    def test_cumulative_wins_show_wins_and_keep_legacy_block_wording_distinct(self):
        for goal, expected_label, compact in (
            (WishGoal(WishObjective.TOTAL_WINS, 3), "Siege sammeln", "2/3 Siege"),
            (WishGoal(WishObjective.BLOCK_MAJORITY, 3), "Insgesamt gewinnen",
             "2/3 Runden"),
        ):
            total = goal.objective == WishObjective.TOTAL_WINS
            rounds, wins = (5, 2) if total else (2, 1)
            state = PetState(wishes=WishState(active=(ActiveWish(
                1, WishId.WIN_OVERALL, "blackjack", 0, 14400,
                game=GameWishProgress(tuple(f"a:{i}" for i in range(rounds)),
                                      wins, 1, None, rounds), goal=goal,
            ),)))
            view = project_hover(snapshot_pet(state), context_at(1800000000),
                                 ComputerSnapshot(), observe_computer=False)
            wish = view.emotional.wishes[0]
            self.assertEqual(wish.label, expected_label)
            self.assertEqual(wish_progress(wish, compact=True), compact)
            self.assertIn("5 Runden" if total else "2/3 Runden", wish_progress(wish))

    def test_each_wish_form_exposes_inner_spoken_target_and_objective_progress(self):
        for key, definition in WISH_CATALOG.definitions.items():
            with self.subTest(wish=key):
                wish = ActiveWish(
                    1,
                    key,
                    definition.targets[0],
                    0,
                    14400,
                    game=GameWishProgress(("session:1",), 1),
                    goal=definition.goal,
                )
                state = PetState(lived_seconds=3600, wishes=WishState(active=(wish,)))
                read = snapshot_pet(state).wishes[0]
                self.assertEqual(read.definition_id, key)
                self.assertEqual(read.remaining_seconds, 10800)
                self.assertFalse(read.expressed)
                self.assertEqual(read.target_id, definition.targets[0])
                if read.game is not None:
                    self.assertEqual(read.game.completed_rounds, 1)
                    self.assertEqual(read.game.wins, 1)
                set_test_pet_values(
                    state, wishes=WishState(active=(replace(wish, expressed_at=3000),))
                )
                self.assertTrue(snapshot_pet(state).wishes[0].expressed)
                view = project_hover(
                    snapshot_pet(state),
                    context_at(1_800_000_000),
                    ComputerSnapshot(),
                    observe_computer=False,
                )
                self.assertTrue(view.emotional.wishes[0].target_label)

    def test_restrictions_reuse_current_capabilities_without_changing_deadlines(self):
        for key, target, context, restriction in (
            (WishId.FACT, "fact", WishContext(), WishRestriction.ONLINE_UNAVAILABLE),
            (
                WishId.PET,
                "pet",
                WishContext(petting_welcome=False),
                WishRestriction.PETTING_UNWELCOME,
            ),
            (
                WishId.WIN_ROUND,
                "blackjack",
                WishContext(games_ready=False),
                WishRestriction.GAME_TIRED,
            ),
        ):
            with self.subTest(wish=key):
                state = PetState(
                    wishes=WishState(active=(ActiveWish(1, key, target, 0, 14400),))
                )
                before = state.capture_checkpoint()
                read = snapshot_pet(state, wish_context=context)
                self.assertEqual(read.wishes[0].restriction, restriction)
                self.assertEqual(read.wishes[0].remaining_seconds, 14400)
                self.assertEqual(state.capture_checkpoint(), before)
        ready = WishContext(online_social=True, prepared_social=frozenset({"fact"}))
        state = PetState(
            wishes=WishState(active=(ActiveWish(1, WishId.FACT, "fact", 0, 14400),))
        )
        self.assertIsNone(snapshot_pet(state, wish_context=ready).wishes[0].restriction)

    def test_paused_stages_have_no_fabricated_expiry_or_recovery(self):
        state = PetState(
            lived_seconds=600,
            moodlets=MoodletState(
                active=(
                    MoodletEpisode(
                        1,
                        MoodletId.HUNGER_WORN,
                        3,
                        0,
                        0,
                        3600,
                        decay_paused=True,
                        recovery_since=500,
                        attribution=MoodletAttribution.USER,
                    ),
                )
            ),
        )
        read = snapshot_pet(state)
        self.assertEqual(read.moodlets[0].remaining_stage_seconds, 3600)
        self.assertEqual(read.moodlets[0].remaining_decay_seconds, 18000)
        self.assertEqual(read.moodlets[0].recovery_wait_seconds, 1700)
        self.assertTrue(read.moodlets[0].decay_paused)
        self.assertEqual(read.moodlets[0].attribution, MoodletAttribution.USER)
        self.assertEqual(snapshot_pet(state), read)

    def test_reads_are_deeply_immutable_and_detached_from_later_aggregate_changes(self):
        state = PetState(
            moodlets=MoodletState(
                active=(MoodletEpisode(1, MoodletId.POKING, 2, 0, 0, 3600),)
            ),
            wishes=WishState(active=(ActiveWish(1, WishId.FOOD, "apple", 0, 14400),)),
        )
        read = snapshot_pet(state)
        self.assertEqual(read.emotions.primary, EmotionalState.IRRITATED)
        with self.assertRaises(FrozenInstanceError):
            setattr(read.moodlets[0], "level", 3)
        with self.assertRaises(FrozenInstanceError):
            setattr(read.wishes[0], "expressed", True)
        set_test_pet_values(state, moodlets=MoodletState(), wishes=WishState())
        self.assertEqual(len(read.emotions.influences), 1)
        self.assertEqual(read.moodlets[0].level, 2)
        self.assertFalse(read.wishes[0].expressed)
