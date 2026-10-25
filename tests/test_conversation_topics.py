"""Evidence selection is bounded, weighted per episode and free of talk history."""

import random
import unittest
from dataclasses import replace
from unittest.mock import Mock

from test_wish_assignment import wish

from aiko_pet.pet.care_evidence import CarePeriodSummary
from aiko_pet.pet.mind.conversation_topics import (
    ConversationKind,
    select_conversation_topic,
)
from aiko_pet.pet.moodlets import (
    MoodletCause,
    MoodletCauseKind,
    MoodletEpisode,
    MoodletGameResult,
    MoodletId,
    MoodletOutcome,
    MoodletState,
    MoodletWishCause,
)
from aiko_pet.pet.wishes import WishId


def actual(number: int = 1, target: str = "chat") -> MoodletCause:
    return MoodletCause(
        MoodletCauseKind.INTERACTION, number, f"actual:{number}",
        target_id=target, outcome=MoodletOutcome.COMPLETED,
    )


def episode(number, family, level=1, *causes):
    return MoodletEpisode(number, family, level, 0, 50, 600, causes=causes)


class ConversationTopicTests(unittest.TestCase):
    def test_intensity_weights_episodes_once_then_selects_one_retained_cause(self):
        strong = episode(1, MoodletId.CONNECTION, 3, actual(1), actual(2), actual(3))
        weak = episode(2, MoodletId.POKING, 1, actual(4, "poking"))
        state = MoodletState(active=(weak, strong))
        rng = Mock(spec=random.Random)
        rng.choices.side_effect = lambda population, **_kw: [population[0]]
        rng.choice.side_effect = lambda population: population[-1]
        selected = select_conversation_topic(state, rng=rng, elapsed=100)
        self.assertEqual(rng.choices.call_args.kwargs["weights"], [3, 1])
        self.assertEqual(selected.episode_id, strong.instance_id)
        self.assertIs(selected.cause, strong.causes[-1])
        self.assertEqual(selected.kind, ConversationKind.SOCIAL)
        self.assertEqual(state.active, (weak, strong))

    def test_both_polarities_remain_eligible_without_negative_priority(self):
        good = episode(1, MoodletId.CONNECTION, 1, actual())
        bad = episode(2, MoodletId.POKING, 1, actual(2, "poking"))
        rng = Mock(spec=random.Random)
        rng.choice.side_effect = lambda population: population[0]
        rng.choices.side_effect = lambda population, **_kw: [population[0]]
        state = MoodletState(active=(bad, good))
        self.assertEqual(select_conversation_topic(state, rng=rng, elapsed=100).kind,
                         ConversationKind.SOCIAL)
        rng.choices.side_effect = lambda population, **_kw: [population[1]]
        self.assertEqual(select_conversation_topic(state, rng=rng, elapsed=100).kind,
                         ConversationKind.NEGATIVE)
        self.assertEqual(rng.choices.call_args.kwargs["weights"], [1, 1])

    def test_same_event_in_multiple_moodlets_is_one_topic_in_strongest_episode(self):
        shared = actual()
        state = MoodletState(active=(
            episode(1, MoodletId.CONNECTION, 1, shared),
            episode(2, MoodletId.ENTHUSIASTIC, 3, shared),
        ))
        rng = Mock(spec=random.Random)
        rng.choices.side_effect = lambda population, **_kw: [population[0]]
        rng.choice.side_effect = lambda population: population[0]
        topic = select_conversation_topic(state, rng=rng, elapsed=100)
        self.assertEqual(topic.episode_id, 2)
        self.assertEqual(rng.choices.call_args.kwargs["weights"], [3])
        self.assertEqual(len(rng.choice.call_args.args[0]), 1)

    def test_legacy_expired_future_and_unspecified_events_do_not_invent_topics(self):
        episodes = (
            episode(1, MoodletId.CONNECTION),
            replace(episode(2, MoodletId.CONNECTION, 1, actual()), remaining_seconds=0),
            episode(3, MoodletId.CONNECTION, 1, replace(actual(), occurred_at=101)),
            episode(4, MoodletId.CONNECTION, 1, actual(4, "unrecorded")),
        )
        selected = select_conversation_topic(
            MoodletState(active=episodes), rng=random.Random(2), elapsed=100,
        )
        self.assertEqual(selected.kind, ConversationKind.STATE)
        self.assertIsNone(selected.cause)

    def test_topic_remains_eligible_after_being_selected_without_a_discussed_flag(self):
        state = MoodletState(active=(episode(1, MoodletId.CONNECTION, 1, actual()),))
        rng = random.Random(12)
        first = select_conversation_topic(state, rng=rng, elapsed=100)
        self.assertEqual(select_conversation_topic(state, rng=rng, elapsed=100), first)
        self.assertEqual(select_conversation_topic(
            replace(state, active=()), rng=rng, elapsed=100,
        ).kind, ConversationKind.STATE)

    def test_only_live_previously_disclosed_wishes_are_present_tense_fallback(self):
        hidden = wish(WishId.CHAT, "chat")
        known = replace(hidden, expressed_at=20)
        for wishes, expected in (
            ((hidden,), ConversationKind.STATE), ((known,), ConversationKind.WISH),
            ((replace(known, expires_at=99),), ConversationKind.STATE),
        ):
            topic = select_conversation_topic(
                MoodletState(), rng=random.Random(0), elapsed=100,
                disclosed_wishes=wishes,
            )
            self.assertEqual(topic.kind, expected)
            self.assertIsNone(topic.cause)
        concrete = MoodletState(active=(episode(1, MoodletId.POKING, 1,
                                                actual(2, "poking")),))
        self.assertEqual(select_conversation_topic(
            concrete, rng=random.Random(0), elapsed=100, disclosed_wishes=(known,),
        ).kind, ConversationKind.NEGATIVE)

    def test_cumulative_goal_keeps_original_objective_distinct_from_final_round(self):
        cause = replace(
            actual(target="blackjack"), kind=MoodletCauseKind.WISH_FULFILLED,
            outcome=MoodletOutcome.WIN,
            wish=MoodletWishCause(1, "win_overall", "blackjack", "total_wins", 2),
            game=MoodletGameResult(MoodletOutcome.DRAW, 4, 2, 1),
        )
        topic = select_conversation_topic(MoodletState(active=(
            episode(1, MoodletId.PRIDE, 1, cause),
        )), rng=random.Random(0), elapsed=100)
        self.assertEqual(topic.key, "game.cumulative")
        self.assertIs(topic.cause, cause)
        self.assertIsNotNone(topic.cause.wish if topic.cause else None)

    def test_period_topics_keep_actual_facts_without_inventing_incidents(self):
        period = CarePeriodSummary(0, 50, encounters=3, fulfilled_wishes=2)
        for family, cause, kind in (
            (MoodletId.HUNGER_WORN,
             replace(actual(target="satiety"), kind=MoodletCauseKind.POOR_CARE),
             ConversationKind.POOR_CARE),
            (MoodletId.TRUSTING,
             replace(actual(), kind=MoodletCauseKind.LONG_TERM, period=period,
                     target_id=None),
             ConversationKind.LONG_TERM),
        ):
            topic = select_conversation_topic(MoodletState(active=(
                episode(1, family, 1, cause),
            )), rng=random.Random(0), elapsed=100)
            self.assertEqual(topic.kind, kind)
            self.assertIs(topic.cause, cause)
        unknown = replace(cause, period=None)
        self.assertEqual(select_conversation_topic(MoodletState(active=(
            episode(1, MoodletId.TRUSTING, 1, unknown),
        )), rng=random.Random(0), elapsed=100).kind, ConversationKind.STATE)

    def test_older_blackjack_loss_without_cards_does_not_prove_a_bust(self):
        cause = replace(actual(target="blackjack"), outcome=MoodletOutcome.LOSS)
        topic = select_conversation_topic(MoodletState(active=(
            episode(1, MoodletId.DISAPPOINTED, 1, cause),
        )), rng=random.Random(0), elapsed=100)
        self.assertEqual(topic.key, "game.blackjack.loss")


if __name__ == "__main__":
    unittest.main()
