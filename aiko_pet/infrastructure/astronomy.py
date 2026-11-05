"""Offline Astronomy Engine adapter; astronomical facts, never authored prose."""

from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from importlib.metadata import version
from typing import Callable, Protocol, cast

from ..pet.horoscope import SkySnapshot, normalized_angle


class _Ecliptic(Protocol):
    elon: float


class _TimeFactory(Protocol):
    def Make(  # noqa: N802 - foreign API
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        second: float,
    ) -> object: ...


class _Astronomy(Protocol):
    Time: _TimeFactory
    SunPosition: Callable[[object], _Ecliptic]
    GeoMoon: Callable[[object], object]
    Ecliptic: Callable[[object], _Ecliptic]
    MoonPhase: Callable[[object], float]


class AstronomyEngineCalculator:
    def calculate(self, instant_utc: datetime) -> SkySnapshot:
        if instant_utc.utcoffset() is None:
            raise ValueError("Astronomy requires an aware UTC instant")
        instant = instant_utc.astimezone(timezone.utc)
        engine = cast(_Astronomy, import_module("astronomy"))
        time = engine.Time.Make(
            instant.year,
            instant.month,
            instant.day,
            instant.hour,
            instant.minute,
            instant.second + instant.microsecond / 1_000_000,
        )
        return SkySnapshot(
            instant,
            normalized_angle(engine.SunPosition(time).elon),
            normalized_angle(engine.Ecliptic(engine.GeoMoon(time)).elon),
            normalized_angle(engine.MoonPhase(time)),
            version("astronomy-engine"),
        )
