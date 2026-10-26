"""Local astronomy, authored coverage and durable daily book lifecycle."""

from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime, timezone
from unittest.mock import Mock

from aiko_pet.application.horoscope_coordinator import HoroscopeCoordinator
from aiko_pet.application.horoscope_models import HoroscopeHistory, daily_request
from aiko_pet.infrastructure.astronomy import AstronomyEngineCalculator
from aiko_pet.infrastructure.horoscope_catalogue import (
    catalogue_coverage,
    load_horoscope_catalogue,
)
from aiko_pet.infrastructure.horoscope_codec import decode_horoscope, encode_horoscope
from aiko_pet.pet.horoscope import (
    ZODIAC_SIGNS,
    DevelopmentDirection,
    SkySnapshot,
    build_profile,
    phase_direction,
    relative_house,
    select_entry,
    sign_at,
)
from aiko_pet.pet.mind.catalog import Reaction

NOW = datetime(2026, 10, 25, 12).timestamp()


def coordinator(history=HoroscopeHistory(), *, persist=lambda: True):
    clock = Mock(return_value=NOW)
    sky = Mock()
    sky.calculate.side_effect = lambda instant: SkySnapshot(
        instant, 210, 30, 180, "fixture"
    )
    credit = Mock(return_value=Mock())
    opening = Reaction.spoken(
        "opening", "Mal sehen, was im Buch steht.", "idle", "horoscope_opening"
    )
    closing = Reaction.spoken(
        "closing", "Das war dein Eintrag.", "idle", "horoscope_closing"
    )
    owner = HoroscopeCoordinator(
        load_horoscope_catalogue(),
        sky,
        sign=lambda: "taurus",
        reactions=lambda entry: (opening, None, closing),
        credit=credit,
        persist=persist,
        history=history,
        wall_time=clock,
    )
    return owner, clock, sky, credit


class HoroscopeTests(unittest.TestCase):
    def test_astronomical_boundaries_and_daily_noon(self):
        self.assertEqual(sign_at(0), "aries")
        self.assertEqual(sign_at(30), "taurus")
        self.assertEqual(sign_at(360), "aries")
        self.assertEqual(relative_house("taurus", "taurus"), 1)
        for angle, direction in (
            (0, "begin"),
            (89.99, "begin"),
            (90, "develop"),
            (180, "reflect"),
            (270, "conclude"),
            (360, "begin"),
        ):
            self.assertEqual(phase_direction(angle), DevelopmentDirection(direction))
        request = daily_request(NOW, "taurus")
        self.assertEqual(request.instant_utc.astimezone().hour, 12)
        sky = AstronomyEngineCalculator().calculate(request.instant_utc)
        self.assertTrue(0 <= sky.sun_longitude < 360)
        self.assertTrue(0 <= sky.moon_longitude < 360)
        self.assertTrue(0 <= sky.phase_degrees < 360)
        # October Sun lies in tropical Scorpio, independent of user sign.
        self.assertEqual(sign_at(sky.sun_longitude), "scorpio")

    def test_reviewed_coverage_stable_selection_and_bubble_limits(self):
        catalogue = load_horoscope_catalogue()
        self.assertEqual(len(catalogue.entries), 96)
        self.assertFalse(catalogue_coverage(catalogue).missing)
        for sign in ZODIAC_SIGNS:
            for phase in (0, 90, 180, 270):
                for moon in range(0, 360, 30):
                    profile = build_profile(
                        sign,
                        SkySnapshot(
                            datetime.now(timezone.utc), 10, moon, phase, "fixture"
                        ),
                    )
                    first = select_entry(catalogue, profile, "stable")
                    reverse = replace(
                        catalogue, entries=tuple(reversed(catalogue.entries))
                    )
                    self.assertEqual(first, select_entry(reverse, profile, "stable"))
                    self.assertIsNotNone(first)
        self.assertTrue(
            all(len(p.text) <= 125 for e in catalogue.entries for p in e.passages)
        )

    def test_partial_resume_replay_and_fixed_expiry_survive_restart(self):
        owner, clock, sky, credit = coordinator()
        day = owner.start("object_1")
        assert day is not None and day.reading is not None
        frozen = day.reading
        self.assertTrue(owner.advance("object_1", owner.generation, 2))
        owner.pause()
        self.assertFalse(owner.advance("object_1", owner.generation - 1, 3))
        self.assertIsNone(owner.put_down("object_1"))
        resumed = owner.start("object_1")
        assert resumed is not None
        self.assertEqual(resumed.index, 2)
        self.assertEqual(credit.call_count, 1)
        owner.advance("object_1", owner.generation, len(frozen.reaction.beats))
        deadline = owner.put_down("object_1")
        self.assertEqual(deadline, NOW + 3600)
        clock.return_value = NOW + 1500
        replay = owner.start("object_1")
        assert replay is not None
        self.assertEqual(replay.index, 0)
        self.assertEqual(owner.put_down("object_1"), deadline)
        restored = decode_horoscope(encode_horoscope(owner.history))
        again, again_clock, again_sky, again_credit = coordinator(restored)
        again_clock.return_value = NOW + 1800
        replay = again.start("object_1")
        assert replay is not None
        self.assertEqual(replay.reading, frozen)
        self.assertFalse(again_sky.calculate.called)
        self.assertFalse(again_credit.called)
        self.assertEqual(sky.calculate.call_count, 1)
        self.assertEqual(credit.call_count, 1)
        again_clock.return_value = deadline
        self.assertIsNone(again.start("object_1"))
        self.assertEqual(again.availability("object_2"), "completed")
        again_clock.return_value = datetime(2026, 10, 26, 12).timestamp()
        self.assertIsNotNone(again.start("object_2"))

    def test_persistence_failure_rolls_back_admission_and_care(self):
        owner, _clock, _sky, credit = coordinator(persist=lambda: False)
        self.assertIsNone(owner.start("object_1"))
        self.assertFalse(owner.history.days)
        credit.return_value.assert_called_once_with()

    def test_old_api_prose_is_discarded_without_double_credit(self):
        raw = dict(
            date="2026-10-25",
            attempts=1,
            index=2,
            admitted=True,
            completed=False,
            reading=dict(
                date="2026-10-25",
                sign="aries",
                overview="Old provider prose",
                advice="",
                disclaimer="",
                footer="",
            ),
        )
        history = decode_horoscope(raw)
        self.assertIsNone(history.days[0].reading)
        owner, _clock, _sky, credit = coordinator(history)
        day = owner.start("object_1")
        assert day is not None
        self.assertEqual(day.sign, "aries")
        self.assertFalse(credit.called)

    def test_each_comment_anchor_has_four_stages_and_omits_tense_state(self):
        from aiko_pet.infrastructure.character_mind import make_aiko_mind
        from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
        from aiko_pet.pet.mind.dialogue_context import DialogueContext, FriendshipStage
        from aiko_pet.pet.routine import context_at

        book = make_aiko_mind(started_at=0).book
        keys = {
            p.comment_key
            for e in load_horoscope_catalogue().entries
            for p in e.passages
            if p.comment_key
        }
        self.assertEqual(len(keys), 24)
        for key in keys:
            for stage in FriendshipStage:
                context = DialogueContext(
                    stage,
                    50,
                    EmotionalComposition(EmotionalState.CALM),
                    context_at(NOW),
                    horoscope_comment_key=key,
                )
                self.assertIsNotNone(book.choose("horoscope_comment", context, 0))
                self.assertIsNone(
                    book.choose(
                        "horoscope_comment",
                        replace(
                            context, emotions=EmotionalComposition(EmotionalState.TENSE)
                        ),
                        0,
                    )
                )

    def test_midnight_replay_and_new_book_do_not_change_the_old_story(self):
        owner, clock, _sky, credit = coordinator()
        clock.return_value = datetime(2026, 10, 25, 23, 50).timestamp()
        day = owner.start("object_1")
        assert day is not None and day.reading is not None
        owner.advance("object_1", owner.generation, len(day.reading.reaction.beats))
        deadline = owner.put_down("object_1")
        clock.return_value = datetime(2026, 10, 26, 0, 10).timestamp()
        new_day = owner.start("object_2")
        assert new_day is not None
        self.assertEqual(new_day.date, "2026-10-26")
        replay = owner.start("object_1")
        assert replay is not None
        self.assertEqual(replay.reading, day.reading)
        self.assertEqual(owner.put_down("object_1"), deadline)
        self.assertEqual(len(owner.history.days), 2)
        self.assertEqual(credit.call_count, 2)

    def test_expired_generation_cannot_advance_at_deadline(self):
        owner, clock, _sky, _credit = coordinator()
        day = owner.start("object_1")
        assert day is not None and day.reading is not None
        owner.advance("object_1", owner.generation, len(day.reading.reaction.beats))
        deadline = owner.put_down("object_1")
        owner.start("object_1")
        clock.return_value = deadline
        self.assertFalse(owner.advance("object_1", owner.generation, 1))

    def test_raised_save_failure_rolls_back_history_and_the_credit(self):
        owner, _clock, _sky, credit = coordinator(
            persist=Mock(side_effect=OSError("disk"))
        )
        with self.assertRaises(OSError):
            owner.start("object_1")
        self.assertFalse(owner.history.days)
        credit.return_value.assert_called_once_with()

    def test_unfinished_previous_day_is_retired_without_becoming_new_reading(self):
        owner, clock, _sky, _credit = coordinator()
        owner.start("object_1")
        clock.return_value = datetime(2026, 10, 26, 12).timestamp()
        self.assertEqual(owner.obsolete_books(), ("object_1",))
        self.assertIsNone(owner.start("object_1"))
