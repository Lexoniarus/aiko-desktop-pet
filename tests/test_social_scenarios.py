"""Deterministic, multi-event behaviour scenarios for Aiko v0.10.

Do not assert one specific randomly selected quote. Assert that her *reason* to
speak follows observations, that silence is real, and that no unobserved
program/user activity can be invented.
"""

import json
import random
import re
import unittest
from datetime import datetime

from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.emotions import EmotionalState
from aiko_pet.pet.mind.adaptive_models import Behaviour
from aiko_pet.pet.mind.adaptive_policy import ActivityMode
from aiko_pet.pet.mind.catalog import CATALOGUE, DialogueBook, Line, Reaction
from aiko_pet.pet.mind.dialogue_context import ReactionTone, SituationalCondition
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from tools.pet_test_support import set_test_pet_values


def require_reaction(value: Reaction | None) -> Reaction:
    """Fail immediately if an expected authored dialogue is unavailable."""
    assert value is not None, "Expected a dialogue reaction"
    return value


def clock(hour=15, day="2026-10-12"):
    dt = datetime.fromisoformat(f"{day}T{hour:02d}:00:00").astimezone()
    return context_at(dt.timestamp())


def scene(
    *,
    mode: ActivityMode = "working",
    duration=1800,
    strain=35,
    effort=0.88,
    expected=None,
    confident=False,
    present=True,
    rest=0,
    uptime=24,
):
    return Behaviour(
        mode=mode,
        strain=strain,
        effort=effort,
        expected_effort=expected,
        expectation_confident=confident,
        present=present,
        uptime_hours=uptime,
        prolonged_work_seconds=duration,
        rest_seconds=rest,
    )


class ClickStoryTests(unittest.TestCase):
    def setUp(self):
        self.mind = make_aiko_mind(started_at=0, rng=random.Random(21))
        self.state = PetState()
        self.context = clock()

    def test_normal_burst_escalates_through_awareness_boundaries_to_silence(self):
        events = [
            (self.mind.click("left", self.state, self.context, 20 + i) or None)
            for i in range(11)
        ]
        self.assertEqual(
            [r.event if r else None for r in events],
            [
                "click_left",
                "click_left",
                "click_notice",
                "rapid_click",
                "rapid_click",
                "click_boundary",
                "click_boundary",
                "click_last_word",
                None,
                None,
                None,
            ],
        )
        self.assertEqual(self.mind.reaction_tone(30), ReactionTone.IRRITATED)
        self.assertEqual(
            require_reaction(
                self.mind.click("right", self.state, self.context, 50)
            ).event,
            "click_right",
        )
        self.assertEqual(
            self.mind.emotional_state(self.state).primary, EmotionalState.SATISFIED
        )

    def test_good_mood_turns_provocation_into_playful_teasing(self):
        set_test_pet_values(self.state, mood=94)
        set_test_pet_values(self.state, energy=90)
        events = [
            require_reaction(self.mind.click("left", self.state, self.context, 50 + i))
            for i in range(8)
        ]
        self.assertEqual(
            [r.event for r in events],
            [
                "click_left",
                "click_left",
                "click_notice_playful",
                "click_tease",
                "click_tease",
                "click_tease_more",
                "click_tease_more",
                "click_last_word",
            ],
        )
        self.assertIn(
            SituationalCondition.PLAYFUL,
            self.mind.dialogue_context(
                self.state, context_at(1800000000), 58
            ).situational_conditions,
        )

    def test_low_energy_and_recent_care_change_early_clicks(self):
        set_test_pet_values(self.state, energy=19)
        self.assertEqual(
            require_reaction(
                self.mind.click("left", self.state, self.context, 20)
            ).event,
            "click_sleepy",
        )
        new_mind = make_aiko_mind(started_at=0.0, rng=random.Random(1))
        new_mind.record_accepted_care("pet", 30)
        self.assertEqual(
            require_reaction(
                new_mind.click("left", PetState(), self.context, 35)
            ).event,
            "click_flustered",
        )
        self.assertEqual(
            require_reaction(
                new_mind.click("left", PetState(), self.context, 100)
            ).event,
            "click_left",
        )

    def test_withdrawn_aiko_stops_earlier_without_forced_jokes(self):
        set_test_pet_values(self.state, mood=12)
        events = [
            self.mind.click("left", self.state, self.context, 100 + i) for i in range(9)
        ]
        self.assertEqual(
            [r.event if r else None for r in events],
            [
                "click_withdrawn",
                "click_withdrawn",
                "click_notice_withdrawn",
                "click_withdrawn_boundary",
                "click_withdrawn_boundary",
                "click_last_word",
                None,
                None,
                None,
            ],
        )

    def test_calm_night_clicks_know_time_without_claiming_work(self):
        night = clock(hour=2)
        reactions = [
            require_reaction(self.mind.click("left", self.state, night, 20 + i))
            for i in range(3)
        ]
        self.assertEqual(
            [r.event for r in reactions], ["click_night", "click_night", "click_notice"]
        )
        self.assertTrue(
            all("CPU" not in r.text and "GPU" not in r.text for r in reactions)
        )

    def test_sleep_requests_quiet_before_requesting_a_wake_transition(self):
        set_test_pet_values(self.state, sleeping=True)
        for i in range(3):
            r = self.mind.click("left", self.state, self.context, 30 + i)
            assert r is not None
            self.assertEqual(r.event, "sleep_click")
            self.assertFalse(self.mind.click_wakes)
        self.assertIsNone(self.mind.click("left", self.state, self.context, 33))
        self.assertTrue(self.mind.click_wakes)
        # The application commits waking; dialogue selection cannot mutate her.
        self.assertTrue(self.state.sleeping)
        self.assertEqual(self.mind.irritation_reaction_until, -1)

    def test_work_interruption_and_recovery_payoff(self):
        self.mind.set_situation(scene(duration=150), now=20)
        events = [
            require_reaction(
                self.mind.click("right", self.state, self.context, 23 + i)
            ).event
            for i in range(7)
        ]
        self.assertEqual(
            events,
            [
                "click_during_work",
                "click_during_work",
                "click_work_repeat",
                "click_work_repeat",
                "click_work_boundary",
                "click_work_boundary",
                "click_last_word",
            ],
        )
        self.assertIsNone(self.mind.click("right", self.state, self.context, 30))
        self.mind.set_situation(
            scene(mode="recovering", effort=0.1, duration=0), now=41
        )
        finish = self.mind.select_computer_reaction(
            "computer_effort_recovered_peak",
            self.state,
            self.context,
            41,
        )
        assert finish is not None
        self.assertEqual(finish.event, "work_finished_interrupted")
        self.assertEqual(
            require_reaction(
                self.mind.click("left", self.state, self.context, 65)
            ).event,
            "click_after_work",
        )
        # A second recovery observation cannot reuse the same interruptions.
        later = self.mind.select_computer_reaction(
            "computer_effort_recovered",
            self.state,
            self.context,
            70,
        )
        assert later is not None
        self.assertEqual(later.event, "computer_effort_recovered")

    def test_long_session_generates_contextual_after_work_thought_once(self):
        self.mind.set_situation(scene(duration=2600), now=500)
        self.mind.set_situation(
            scene(mode="recovering", duration=0, effort=0.08), now=505
        )
        event = self.mind.select_computer_reaction(
            "computer_effort_recovered_peak",
            self.state,
            self.context,
            505,
        )
        assert event is not None
        self.assertEqual(event.event, "work_finished_long")
        self.assertEqual(
            require_reaction(
                self.mind.select_spontaneous_reaction(self.state, self.context, 760)
            ).event,
            "after_work_thought",
        )
        self.assertNotEqual(
            require_reaction(
                self.mind.select_spontaneous_reaction(self.state, self.context, 770)
            ).event,
            "after_work_thought",
        )
        self.assertNotEqual(
            require_reaction(
                self.mind.select_spontaneous_reaction(self.state, self.context, 1500)
            ).event,
            "after_work_thought",
        )

    def test_no_fake_work_recovery_after_short_spike(self):
        self.mind.set_situation(scene(duration=8), now=500)
        self.mind.click("left", self.state, self.context, 501)
        self.mind.click("left", self.state, self.context, 502)
        self.mind.set_situation(scene(mode="present", duration=0, effort=0.1), now=507)
        event = self.mind.select_computer_reaction(
            "computer_effort_recovered", self.state, self.context, 508
        )
        assert event is not None
        self.assertNotIn(
            event.event, ("work_finished_long", "work_finished_interrupted")
        )

    def test_unusual_load_requires_trustworthy_learned_profile(self):
        mind = self.mind
        mind.set_situation(scene(expected=0.09, confident=True, effort=0.69), now=100)
        reaction = mind.select_computer_reaction(
            "computer_effort_heavy", self.state, self.context, 102
        )
        assert reaction is not None
        self.assertEqual(reaction.event, "work_unexpected")
        mind.set_situation(scene(expected=0.09, confident=False, effort=0.69), now=120)
        reaction = mind.select_computer_reaction(
            "computer_effort_heavy", self.state, self.context, 122
        )
        assert reaction is not None
        self.assertEqual(reaction.event, "computer_effort_heavy")

    def test_night_work_and_actual_overnight_rest_differ(self):
        night = clock(hour=2)
        self.mind.set_situation(scene(strain=66, effort=0.9), now=400)
        self.assertEqual(
            require_reaction(
                self.mind.select_spontaneous_reaction(self.state, night, 405)
            ).event,
            "work_late",
        )
        self.mind.set_situation(
            scene(
                mode="resting",
                duration=0,
                strain=3,
                effort=0.08,
                present=False,
                rest=6 * 3600,
                uptime=120,
            ),
            now=410,
        )
        # A long effort may leave one reflective thought, but the memory is
        # bounded; later quiet is simply quiet, not phantom continued work.
        self.assertEqual(
            require_reaction(
                self.mind.select_spontaneous_reaction(self.state, night, 600)
            ).event,
            "after_work_thought",
        )
        self.assertEqual(
            require_reaction(
                self.mind.select_spontaneous_reaction(self.state, night, 1200)
            ).event,
            "quiet_alone",
        )
        uptime = self.mind.select_computer_reaction(
            "computer_uptime",
            self.state,
            night,
            605,
        )
        assert uptime is not None
        self.assertEqual(uptime.event, "computer_uptime_grounded")
        self.assertNotIn("CPU", uptime.text)

    def test_return_respects_work_and_observed_recent_recovery(self):
        self.mind.set_situation(scene(), now=30)
        self.assertEqual(
            require_reaction(
                self.mind.return_to_pet(self.state, self.context, 30 * 60)
            ).event,
            "return_working",
        )
        self.mind.set_situation(
            scene(mode="recovering", duration=0, effort=0.08), now=1810
        )
        self.assertEqual(
            self.mind.return_to_pet(self.state, self.context, 30 * 60 + 10), None
        )
        # No unobserved absence is invented during a 10 second gap.
        self.mind.last_contact = 0
        self.assertEqual(
            require_reaction(
                self.mind.return_to_pet(self.state, self.context, 1820)
            ).event,
            "return_after_work",
        )

    def test_unavailable_situation_does_not_invent_usage(self):
        self.mind.set_situation(None)
        reaction = self.mind.select_spontaneous_reaction(self.state, self.context, 100)
        assert reaction is not None
        self.assertNotIn(
            reaction.event,
            (
                "work_concentrating",
                "work_late",
                "work_long_thought",
                "work_finished_long",
                "return_working",
            ),
        )


class CatalogueContractTests(unittest.TestCase):
    def test_followup_schema_and_nonexistent_animation_rejected(self):
        raw = json.loads(CATALOGUE.read_text(encoding="utf-8"))["lines"][0]
        for key, bad in [
            ("followup_text", ""),
            ("followup_delay_ms", 200),
            ("followup_delay_ms", 4000),
            ("followup_text", "A" * 130),
            ("animation", "crying"),
        ]:
            with self.subTest(key=key, bad=bad):
                data = dict(raw, **{key: bad})
                with self.assertRaises(ValueError):
                    Line.parse(data)

    def test_sequence_copy_is_short_and_hardware_has_observation_context(self):
        for line in DialogueBook.from_file().lines:
            for beat in line.beats:
                if beat.kind != "text":
                    continue
                self.assertLessEqual(len(beat.content), 125)
                for forbidden in ("Academy", "Kobe"):
                    self.assertIsNone(
                        re.search(
                            r"\b" + re.escape(forbidden) + r"\b",
                            beat.content,
                            flags=re.IGNORECASE,
                        )
                    )
                if re.search(r"\b(CPU|GPU|RAM)\b", beat.content, re.IGNORECASE):
                    self.assertTrue(
                        line.event.startswith("computer_")
                        or line.event in {"work_long_thought", "pet_during_work"},
                        line.id,
                    )

    def test_all_new_events_have_actual_authored_lines(self):
        book = DialogueBook.from_file()
        event_set = {line.event for line in book.lines}
        expected = (
            "click_notice",
            "click_notice_playful",
            "click_notice_withdrawn",
            "click_withdrawn",
            "click_withdrawn_boundary",
            "click_night",
            "click_weary",
            "click_tease",
            "click_tease_more",
            "click_boundary",
            "click_last_word",
            "click_sleepy",
            "click_flustered",
            "click_during_work",
            "click_work_repeat",
            "click_work_boundary",
            "click_after_work",
            "work_finished_interrupted",
            "work_finished_long",
            "work_unexpected",
            "work_late",
            "work_long_thought",
            "work_concentrating",
            "after_work_thought",
            "return_working",
            "return_after_work",
            "quiet_alone",
            "quiet_together",
            "pet_during_work",
            "computer_uptime_grounded",
        )
        for event in expected:
            with self.subTest(event=event):
                self.assertIn(event, event_set)
                self.assertGreaterEqual(sum(x.event == event for x in book.lines), 3)


if __name__ == "__main__":
    unittest.main()
