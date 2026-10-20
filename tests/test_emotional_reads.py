"""Passive snapshots expose the full emotional model without running transitions."""

import unittest
from dataclasses import FrozenInstanceError, replace

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.pet.emotions import EmotionalState
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import (
    MoodletAttribution,
    MoodletEpisode,
    MoodletId,
    MoodletState,
)
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import (
    ActiveWish,
    GameWishProgress,
    WishContext,
    WishId,
    WishRestriction,
    WishState,
)
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.view_models.projections import project_hover, project_status
from tools.pet_test_support import set_test_pet_values


class EmotionalReadTests(unittest.TestCase):
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
        self.assertEqual(len(status.emotional.moodlets), 18)
        self.assertEqual(len(read.emotions.influences), 18)
        self.assertEqual(
            {m.value.definition_id for m in status.emotional.moodlets}, set(MoodletId)
        )
        self.assertTrue(
            all(m.label and m.description for m in status.emotional.moodlets)
        )
        self.assertEqual(state.capture_checkpoint(), before)

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
