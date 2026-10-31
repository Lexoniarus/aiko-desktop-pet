"""Strict explicit-file loading for the authored offline horoscope book."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from ..pet.catalog_validation import load_json, object_fields
from ..pet.horoscope import (
    ZODIAC_SIGNS,
    BookPassage,
    DevelopmentDirection,
    EntryEligibility,
    HoroscopeCatalogue,
    HoroscopeEntry,
    HoroscopeTheme,
)

CATALOGUE = Path(__file__).resolve().parents[1] / "data/horoscope/de/index.json"


def _strings(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list) or any(not isinstance(v, str) for v in raw):
        raise ValueError("Expected an explicit string list")
    return tuple(raw)


def _passage(raw: Any) -> BookPassage:
    value = object_fields(
        raw, ("id", "text"), optional=("comment_key",), context="book passage"
    )
    if (
        not isinstance(value["id"], str)
        or not isinstance(value["text"], str)
        or (
            value.get("comment_key") is not None
            and not isinstance(value["comment_key"], str)
        )
    ):
        raise ValueError("Invalid book passage fields")
    return BookPassage(value["id"], value["text"], value.get("comment_key"))


def _entry(raw: Any) -> HoroscopeEntry:
    value = object_fields(
        raw,
        (
            "id",
            "revision",
            "theme",
            "direction",
            "variant",
            "allowed_signs",
            "eligibility",
            "passages",
        ),
        context="book entry",
    )
    if (
        any(
            not isinstance(value[k], str)
            for k in ("id", "theme", "direction", "variant")
        )
        or type(value["revision"]) is not int
        or not isinstance(value["passages"], list)
    ):
        raise ValueError("Invalid book entry fields")
    rule = object_fields(
        value["eligibility"],
        (),
        optional=(
            "sun_signs",
            "moon_signs",
            "sun_houses",
            "moon_houses",
        ),
        context="book eligibility",
    )
    houses: dict[str, tuple[int, ...]] = {}
    for name in ("sun_houses", "moon_houses"):
        values = rule.get(name, [])
        if not isinstance(values, list) or any(type(v) is not int for v in values):
            raise ValueError("Invalid house list")
        houses[name] = tuple(values)
    return HoroscopeEntry(
        value["id"],
        value["revision"],
        HoroscopeTheme(value["theme"]),
        DevelopmentDirection(value["direction"]),
        value["variant"],
        _strings(value["allowed_signs"]),
        tuple(_passage(passage) for passage in value["passages"]),
        EntryEligibility(
            _strings(rule.get("sun_signs", [])),
            _strings(rule.get("moon_signs", [])),
            houses["sun_houses"],
            houses["moon_houses"],
        ),
    )


def load_horoscope_catalogue(index_path: Path = CATALOGUE) -> HoroscopeCatalogue:
    index = object_fields(
        load_json(index_path),
        (
            "index_version",
            "catalogue_version",
            "language",
            "catalogue_id",
            "revision",
            "files",
        ),
        context="horoscope index",
    )
    if (
        type(index["index_version"]) is not int
        or index["index_version"] != 1
        or type(index["catalogue_version"]) is not int
        or index["catalogue_version"] != 1
        or index["language"] != "de"
        or not isinstance(index["catalogue_id"], str)
        or type(index["revision"]) is not int
    ):
        raise ValueError("Unsupported book index")
    names = _strings(index["files"])
    if not names or len(set(names)) != len(names):
        raise ValueError("Missing or duplicate book sources")
    root = index_path.parent.resolve()
    entries: list[HoroscopeEntry] = []
    for name in names:
        relative = PurePosixPath(name)
        source = (root / name).resolve()
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or "\\" in name
            or ":" in name
            or relative.suffix != ".json"
            or relative.as_posix() != name
            or not source.is_relative_to(root)
            or source == index_path.resolve()
        ):
            raise ValueError("Unsafe book source path")
        data = object_fields(
            load_json(source),
            (
                "catalogue_version",
                "language",
                "entries",
            ),
            context="book source",
        )
        if (
            type(data["catalogue_version"]) is not int
            or data["catalogue_version"] != 1
            or data["language"] != "de"
            or not isinstance(data["entries"], list)
        ):
            raise ValueError("Unsupported book source")
        entries.extend(_entry(item) for item in data["entries"])
    return HoroscopeCatalogue(index["catalogue_id"], index["revision"], tuple(entries))


@dataclass(frozen=True, slots=True)
class CoverageReport:
    entries: int
    missing: tuple[tuple[str, HoroscopeTheme, DevelopmentDirection], ...]


def catalogue_coverage(catalogue: HoroscopeCatalogue) -> CoverageReport:
    return CoverageReport(
        len(catalogue.entries),
        tuple(
            (sign, theme, direction)
            for sign in ZODIAC_SIGNS
            for theme in HoroscopeTheme
            for direction in DevelopmentDirection
            if not any(
                sign in entry.allowed_signs
                and entry.theme == theme
                and entry.direction == direction
                for entry in catalogue.entries
            )
        ),
    )
