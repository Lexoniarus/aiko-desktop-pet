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

from aiko_pet.adaptive import Behaviour
from aiko_pet.dialogue import AikoMind, CATALOGUE, DialogueBook, Line
from aiko_pet.domain import PetState
from aiko_pet.routine import context_at


def clock(hour=15, day="2026-10-12"):
    dt = datetime.fromisoformat(f"{day}T{hour:02d}:00:00").astimezone()
    return context_at(dt.timestamp())


def scene(*, mode="working", duration=1800, strain=35, effort=0.88,
          expected=None, confident=False, present=True, rest=0,
          uptime=24):
    return Behaviour(
        mode=mode, strain=strain, effort=effort,
        expected_effort=expected, expectation_confident=confident,
        present=present, uptime_hours=uptime,
        prolonged_work_seconds=duration, rest_seconds=rest,
        can_sleep=False, should_wake=False, can_nap=False,
    )


class ClickStoryTests(unittest.TestCase):
    def setUp(self):
        self.mind = AikoMind(rng=random.Random(21), started_at=0)
        self.state = PetState()
        self.context = clock()

    def test_normal_burst_escalates_through_awareness_boundaries_to_silence(self):
        events = [
            (self.mind.click("left", self.state, self.context, 20 + i) or None)
            for i in range(11)
        ]
        self.assertEqual(
            [r.event if r else None for r in events],
            ["click_left", "click_left", "click_notice", "rapid_click",
             "rapid_click", "click_boundary", "click_boundary",
             "click_last_word", None, None, None],
        )
        self.assertEqual(self.mind.emotion(self.state, 30), "irritated")
        self.assertEqual(
            self.mind.click("right", self.state, self.context, 50).event,
            "click_right",
        )
        self.assertEqual(self.mind.emotion(self.state, 50), "calm")

    def test_good_mood_turns_provocation_into_playful_teasing(self):
        self.state.mood = 94
        self.state.energy = 90
        events = [self.mind.click("left", self.state, self.context, 50+i)
                  for i in range(8)]
        self.assertEqual([r.event for r in events], [
            "click_left", "click_left", "click_notice_playful",
            "click_tease", "click_tease", "click_tease_more",
            "click_tease_more", "click_last_word",
        ])
        self.assertEqual(self.mind.emotion(self.state, 58), "playful")

    def test_low_energy_and_recent_care_change_early_clicks(self):
        self.state.energy = 19
        self.assertEqual(
            self.mind.click("left", self.state, self.context, 20).event,
            "click_sleepy",
        )
        new_mind = AikoMind(rng=random.Random(1))
        new_mind.after_care("pet", 30)
        self.assertEqual(
            new_mind.click("left", PetState(), self.context, 35).event,
            "click_flustered",
        )
        self.assertEqual(
            new_mind.click("left", PetState(), self.context, 100).event,
            "click_left",
        )

    def test_withdrawn_aiko_stops_earlier_without_forced_jokes(self):
        self.state.mood = 12
        events = [self.mind.click("left", self.state, self.context, 100 + i)
                  for i in range(9)]
        self.assertEqual([r.event if r else None for r in events], [
            "click_withdrawn", "click_withdrawn", "click_notice_withdrawn",
            "click_withdrawn_boundary", "click_withdrawn_boundary",
            "click_last_word", None, None, None,
        ])

    def test_calm_night_clicks_know_time_without_claiming_work(self):
        night = clock(hour=2)
        reactions = [self.mind.click("left", self.state, night, 20+i)
                     for i in range(3)]
        self.assertEqual([r.event for r in reactions],
                         ["click_night", "click_night", "click_notice"])
        self.assertTrue(all("CPU" not in r.text and "GPU" not in r.text
                            for r in reactions))

    def test_sleep_does_not_wake_and_is_not_click_spam(self):
        self.state.sleeping = True
        for i in range(12):
            r = self.mind.click("left", self.state, self.context, 30+i)
            self.assertEqual(r.event, "sleep_click")
        self.assertTrue(self.state.sleeping)
        self.assertEqual(self.mind.irritated_until, -1)

    def test_work_interruption_and_recovery_payoff(self):
        self.mind.set_situation(scene(duration=150), now=20)
        events = [self.mind.click("right", self.state, self.context, 23+i).event
                  for i in range(7)]
        self.assertEqual(events, ["click_during_work", "click_during_work",
                                  "click_work_repeat", "click_work_repeat",
                                  "click_work_boundary", "click_work_boundary",
                                  "click_last_word"])
        self.assertIsNone(self.mind.click("right", self.state, self.context, 30))
        self.mind.set_situation(scene(mode="recovering", effort=0.1,
                                      duration=0), now=41)
        finish = self.mind.computer_event(
            "computer_effort_recovered_peak", self.state, self.context, 41,
        )
        self.assertEqual(finish.event, "work_finished_interrupted")
        self.assertEqual(self.mind.click("left", self.state, self.context, 65).event,
                         "click_after_work")
        # A second recovery observation cannot reuse the same interruptions.
        later = self.mind.computer_event(
            "computer_effort_recovered", self.state, self.context, 70,
        )
        self.assertEqual(later.event, "computer_effort_recovered")

    def test_long_session_generates_contextual_after_work_thought_once(self):
        self.mind.set_situation(scene(duration=2600), now=500)
        self.mind.set_situation(scene(mode="recovering", duration=0,
                                      effort=0.08), now=505)
        event = self.mind.computer_event(
            "computer_effort_recovered_peak", self.state, self.context, 505,
        )
        self.assertEqual(event.event, "work_finished_long")
        self.assertEqual(self.mind.spontaneous_event(
            self.state, self.context, 760).event, "after_work_thought")
        self.assertNotEqual(self.mind.spontaneous_event(
            self.state, self.context, 770).event, "after_work_thought")
        self.assertNotEqual(self.mind.spontaneous_event(
            self.state, self.context, 1500).event, "after_work_thought")

    def test_no_fake_work_recovery_after_short_spike(self):
        self.mind.set_situation(scene(duration=8), now=500)
        self.mind.click("left", self.state, self.context, 501)
        self.mind.click("left", self.state, self.context, 502)
        self.mind.set_situation(scene(mode="present", duration=0,
                                      effort=0.1), now=507)
        event = self.mind.computer_event(
            "computer_effort_recovered", self.state, self.context, 508)
        self.assertNotIn(event.event, ("work_finished_long",
                                       "work_finished_interrupted"))

    def test_unusual_load_requires_trustworthy_learned_profile(self):
        mind = self.mind
        mind.set_situation(scene(expected=0.09, confident=True,
                                 effort=0.69), now=100)
        reaction = mind.computer_event("computer_effort_heavy",
                                       self.state, self.context, 102)
        self.assertEqual(reaction.event, "work_unexpected")
        mind.set_situation(scene(expected=0.09, confident=False,
                                 effort=0.69), now=120)
        reaction = mind.computer_event("computer_effort_heavy",
                                       self.state, self.context, 122)
        self.assertEqual(reaction.event, "computer_effort_heavy")

    def test_night_work_and_actual_overnight_rest_differ(self):
        night = clock(hour=2)
        self.mind.set_situation(scene(strain=66, effort=0.9), now=400)
        self.assertEqual(self.mind.spontaneous_event(
            self.state, night, 405).event, "work_late")
        self.mind.set_situation(scene(mode="resting", duration=0, strain=3,
                                      effort=0.08, present=False, rest=6*3600,
                                      uptime=120), now=410)
        # A long effort may leave one reflective thought, but the memory is
        # bounded; later quiet is simply quiet, not phantom continued work.
        self.assertEqual(self.mind.spontaneous_event(
            self.state, night, 600).event, "after_work_thought")
        self.assertEqual(self.mind.spontaneous_event(
            self.state, night, 1200).event, "quiet_alone")
        uptime = self.mind.computer_event(
            "computer_uptime", self.state, night, 605,
        )
        self.assertEqual(uptime.event, "computer_uptime_grounded")
        self.assertNotIn("CPU", uptime.text)

    def test_return_respects_work_and_observed_recent_recovery(self):
        self.mind.set_situation(scene(), now=30)
        self.assertEqual(self.mind.return_to_pet(
            self.state, self.context, 30*60).event, "return_working")
        self.mind.set_situation(scene(mode="recovering", duration=0,
                                      effort=0.08), now=1810)
        self.assertEqual(self.mind.return_to_pet(
            self.state, self.context, 30*60+10), None)
        # No unobserved absence is invented during a 10 second gap.
        self.mind.last_contact = 0
        self.assertEqual(self.mind.return_to_pet(
            self.state, self.context, 1820).event, "return_after_work")

    def test_unavailable_situation_does_not_invent_usage(self):
        self.mind.set_situation(None)
        reaction = self.mind.spontaneous_event(self.state, self.context, 100)
        self.assertNotIn(reaction.event, (
            "work_concentrating", "work_late", "work_long_thought",
            "work_finished_long", "return_working",
        ))


class CatalogueContractTests(unittest.TestCase):
    def test_followup_schema_and_nonexistent_animation_rejected(self):
        raw = json.loads(CATALOGUE.read_text(encoding="utf-8"))["lines"][0]
        for key, bad in [("followup_text", ""), ("followup_delay_ms", 200),
                         ("followup_delay_ms", 4000), ("followup_text", "A"*130),
                         ("animation", "crying")]:
            with self.subTest(key=key, bad=bad):
                data = dict(raw, **{key: bad})
                with self.assertRaises(ValueError):
                    Line.parse(data)

    def test_all_followup_text_is_short_and_no_fiction_or_hardware(self):
        lines = DialogueBook.from_file().lines
        for line in lines:
            if not line.followup_text:
                continue
            self.assertLessEqual(len(line.followup_text), 125)
            for forbidden in ("Academy", "Kobe", "GPU", "CPU", "RAM"):
                self.assertIsNone(re.search(
                    r"\b" + re.escape(forbidden) + r"\b",
                    line.followup_text, flags=re.IGNORECASE,
                ))

    def test_all_new_events_have_actual_authored_lines(self):
        book = DialogueBook.from_file()
        event_set = {line.event for line in book.lines}
        expected = (
            "click_notice", "click_notice_playful", "click_notice_withdrawn",
            "click_withdrawn", "click_withdrawn_boundary", "click_night",
            "click_weary", "click_tease",
            "click_tease_more", "click_boundary", "click_last_word",
            "click_sleepy", "click_flustered", "click_during_work",
            "click_work_repeat", "click_work_boundary", "click_after_work",
            "work_finished_interrupted", "work_finished_long",
            "work_unexpected", "work_late", "work_long_thought",
            "work_concentrating", "after_work_thought", "return_working",
            "return_after_work", "quiet_alone", "quiet_together",
            "pet_during_work", "computer_uptime_grounded",
        )
        for event in expected:
            with self.subTest(event=event):
                self.assertIn(event, event_set)
                self.assertGreaterEqual(sum(x.event == event for x in book.lines), 3)


if __name__ == "__main__":
    unittest.main()
