"""Read-only wish catalogue validated against actual activity definitions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Collection, Mapping

from ..games.contracts import GameId
from .catalog_validation import enum_value, integer_value, load_json, object_fields
from .content import GERMAN_TEXT
from .food_catalog import DEFAULT_CATALOG
from .moodlet_catalog import MOODLET_CATALOG, MoodletCatalog
from .moodlets import MoodletGroup, MoodletId, MoodletPolarity
from .wishes import WishArea, WishDefinition, WishId, WishTargetKind


@dataclass(frozen=True, slots=True)
class WishCatalog:
    definitions: Mapping[WishId, WishDefinition]


def _area(key: WishId) -> WishArea:
    """Objective semantics are Python contracts, not executable JSON rules."""
    if key == WishId.FOOD:
        return WishArea.FOOD
    if key == WishId.PET:
        return WishArea.AFFECTION
    if key in (WishId.CHAT, WishId.SINGLE, WishId.TWO_PARTS, WishId.FACT):
        return WishArea.SOCIAL
    return WishArea.GAMES


def parse_wish_catalog(
    raw: Any, *, moodlets: MoodletCatalog = MOODLET_CATALOG,
    food_ids: Collection[str] = DEFAULT_CATALOG.foods,
    game_ids: Collection[str] = tuple(GameId),
    text_keys: Collection[str] = GERMAN_TEXT.messages,
) -> WishCatalog:
    data = object_fields(raw, ("version", "wishes"), context="wishes")
    if type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("Unsupported wish catalogue version")
    rows = data["wishes"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("Wish catalogue must contain objective definitions")
    definitions: dict[WishId, WishDefinition] = {}
    for value in rows:
        row = object_fields(value, (
            "id", "area", "target_kind", "targets", "fulfillment_moodlet",
            "fulfillment_level", "round_count",
        ), context="wish")
        key = enum_value(row["id"], WishId, context="wish.id")
        if key in definitions:
            raise ValueError(f"Duplicate wish ID: {key}")
        area = enum_value(row["area"], WishArea, context=str(key))
        kind = enum_value(row["target_kind"], WishTargetKind, context=str(key))
        if area != _area(key):
            raise ValueError(f"{key}: incorrect objective area")
        expected_kind, allowed_targets, group = {
            WishArea.FOOD: (WishTargetKind.FOOD, food_ids, MoodletGroup.FOOD_WISH),
            WishArea.GAMES: (WishTargetKind.GAME, game_ids, MoodletGroup.GAME_WISH),
            WishArea.SOCIAL: (WishTargetKind.SOCIAL, (key.value,),
                              MoodletGroup.SOCIAL_WISH),
            WishArea.AFFECTION: (WishTargetKind.CARE, (key.value,),
                                 MoodletGroup.AFFECTION_WISH),
        }[area]
        targets = row["targets"]
        if (
            kind != expected_kind or not isinstance(targets, list) or not targets
            or any(not isinstance(t, str) or t not in allowed_targets for t in targets)
            or len(targets) != len(set(targets))
        ):
            raise ValueError(f"{key}: unknown, duplicate or incompatible targets")
        outcome = enum_value(row["fulfillment_moodlet"], MoodletId, context=str(key))
        if outcome not in moodlets.definitions:
            raise ValueError(f"{key}: missing fulfillment Moodlet {outcome}")
        impression = moodlets.definitions[outcome]
        if (impression.polarity != MoodletPolarity.POSITIVE
                or impression.group != group):
            raise ValueError(f"{key}: fulfillment needs a positive {group} Moodlet")
        level = integer_value(row["fulfillment_level"], minimum=1,
                              maximum=len(impression.level_points), context=str(key))
        rounds = integer_value(row["round_count"], minimum=0, maximum=100,
                               context=f"{key}.round_count")
        if ((area == WishArea.GAMES) != (rounds > 0)
                or (key in (WishId.WIN_ROUND, WishId.AVOID_ROUND_LOSS)
                    and rounds != 1)):
            raise ValueError(f"{key}: incompatible round scope")
        definition = WishDefinition(key, area, kind, tuple(targets), outcome,
                                    level, rounds)
        if not {definition.label_key, definition.description_key} <= set(text_keys):
            raise ValueError(f"{key}: missing localized label or description")
        definitions[key] = definition
    if set(definitions) != set(WishId):
        raise ValueError("Wish catalogue must define every supported objective")
    return WishCatalog(MappingProxyType(definitions))


def load_packaged_wish_catalog(
    path: Path = Path(__file__).resolve().parents[1] / "data/wishes.json",
) -> WishCatalog:
    return parse_wish_catalog(load_json(path))


WISH_CATALOG = load_packaged_wish_catalog()
