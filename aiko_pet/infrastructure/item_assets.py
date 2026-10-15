"""Validate the shipped, pre-scaled food and weapon PNG catalog."""

from __future__ import annotations

import json
import struct
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Mapping, cast

from ..asset_paths import ASSET_ROOT
from ..pet.animation.item_assets import HandItem, ItemCatalog, ItemSprite
from ..pet.food_catalog import DEFAULT_CATALOG
from ..pet.content import GERMAN_TEXT

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png(root: Path, name: object) -> tuple[Path, tuple[int, int]]:
    if not isinstance(name, str) or not name:
        raise ValueError("An item PNG needs a relative path")
    path = (root / name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError("An item PNG path escapes the item directory")
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("rb") as image:
        head = image.read(24)
    if len(head) != 24 or head[:8] != PNG_SIGNATURE:
        raise ValueError(f"Not a PNG image: {path}")
    width, height = struct.unpack(">II", head[16:24])
    if width <= 0 or height <= 0 or width > 512 or height > 512:
        raise ValueError(f"Unexpected item PNG dimensions: {path}")
    return path, (width, height)


def _items(root: Path, records: object, *, food: bool) -> Mapping[str, HandItem]:
    if not isinstance(records, list) or not records:
        raise ValueError("Item categories must contain a nonempty list")
    items: dict[str, HandItem] = {}
    for entry in records:
        if not isinstance(entry, dict):
            raise ValueError("Malformed item entry")
        key = entry.get("id")
        if not isinstance(key, str) or not key or not key.isidentifier():
            raise ValueError("Invalid item id")
        if key in items:
            raise ValueError("Duplicate item id")
        if food:
            if "label" in entry:
                raise ValueError("Food labels belong to the nutrition catalogue")
            if key == "energy_drink":
                label = GERMAN_TEXT.format("ui.energy_drink_name")
            else:
                profile = DEFAULT_CATALOG.foods.get(key)
                if profile is None:
                    raise ValueError(f"Food asset has no nutrition entry: {key}")
                label = profile.display_name
        else:
            raw_label = entry.get("label")
            if not isinstance(raw_label, str) or not raw_label.strip():
                raise ValueError("Weapon asset needs a label")
            label = raw_label
        icon = _png(root, entry.get("icon"))[0] if food else None
        variants = entry.get("variants")
        if not isinstance(variants, dict) or set(variants) != {"1", "2"}:
            raise ValueError("Each item needs native 1x and 2x PNGs")
        sprites: dict[int, ItemSprite] = {}
        for scale in (1, 2):
            spec = variants[str(scale)]
            if not isinstance(spec, dict):
                raise ValueError("Malformed item variant")
            path, (width, height) = _png(root, spec.get("path"))
            pivot: Any = spec.get("pivot")
            if (
                not isinstance(pivot, list) or len(pivot) != 2
                or any(type(v) not in (int, float) for v in pivot)
                or not 0 <= pivot[0] <= width
                or not 0 <= pivot[1] <= height
            ):
                raise ValueError(f"Invalid grip point for {key} at {scale}x")
            sprites[scale] = ItemSprite(path, (float(pivot[0]), float(pivot[1])))
        action = entry.get("care_action", "feed" if food else None)
        if food and action not in ("feed", "energy_drink"):
            raise ValueError(f"Unsupported food care action for {key}")
        if not food and action is not None:
            raise ValueError("Weapon items cannot declare a food care action")
        items[key] = HandItem(
            key, label, icon, MappingProxyType(sprites),
            cast(Literal["feed", "energy_drink"] | None, action),
        )
    return MappingProxyType(items)


def load_item_catalog(root: Path = ASSET_ROOT / "items") -> ItemCatalog:
    """Read the prebuilt sprites without Pillow or a runtime network request."""
    data = json.loads((root / "items.json").read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Unsupported item catalog version")
    foods = _items(root, data.get("foods"), food=True)
    weapons = _items(root, data.get("weapons"), food=False)
    if set(foods) != set(DEFAULT_CATALOG.menu_order):
        raise ValueError("Food assets and nutrition menu must have the same IDs")
    if set(foods).intersection(weapons):
        raise ValueError("Item IDs must be unique across categories")
    return ItemCatalog(foods, weapons)
