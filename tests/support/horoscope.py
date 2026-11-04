"""Shared horoscope fixtures without importing test cases."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

from aiko_pet.application.horoscope_coordinator import HoroscopeCoordinator
from aiko_pet.application.horoscope_models import HoroscopeHistory
from aiko_pet.infrastructure.horoscope_catalogue import load_horoscope_catalogue
from aiko_pet.pet.horoscope import SkySnapshot
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
    return (owner, clock, sky, credit)
