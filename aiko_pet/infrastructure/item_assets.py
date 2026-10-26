"""Validate the shipped, pre-scaled food and weapon PNG catalog."""

from __future__ import annotations

import math
import struct
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from ..asset_paths import ASSET_ROOT
from ..pet.animation.item_assets import HandItem, ItemCatalog, ItemSprite, ReadableItem
from ..pet.catalog_validation import load_json, object_fields
from ..pet.content import GERMAN_TEXT
from ..pet.food_catalog import DEFAULT_CATALOG

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
        if "care_action" in entry:
            raise ValueError("Visual assets cannot decide pet care actions")
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
        object_fields(
            entry,
            ("id", "variants", "icon") if food else ("id", "variants", "label"),
            context=f"item {key}",
        )
        icon = _png(root, entry.get("icon"))[0] if food else None
        variants = entry.get("variants")
        if not isinstance(variants, dict) or set(variants) != {"1", "2"}:
            raise ValueError("Each item needs native 1x and 2x PNGs")
        sprites: dict[int, ItemSprite] = {}
        for scale in (1, 2):
            spec = variants[str(scale)]
            if not isinstance(spec, dict):
                raise ValueError("Malformed item variant")
            object_fields(
                spec,
                ("path", "pivot"),
                optional=("display_path",),
                context=f"item {key} {scale}x",
            )
            path, (width, height) = _png(root, spec.get("path"))
            display_path = None
            if "display_path" in spec:
                display_path, display_size = _png(root, spec["display_path"])
                if display_size != (width, height):
                    raise ValueError("An item display copy must preserve dimensions")
            pivot: Any = spec.get("pivot")
            if (
                not isinstance(pivot, list)
                or len(pivot) != 2
                or any(type(v) not in (int, float) for v in pivot)
                or not 0 <= pivot[0] <= width
                or not 0 <= pivot[1] <= height
            ):
                raise ValueError(f"Invalid grip point for {key} at {scale}x")
            sprites[scale] = ItemSprite(
                path, (float(pivot[0]), float(pivot[1])), display_path
            )
        items[key] = HandItem(
            key,
            label,
            icon,
            MappingProxyType(sprites),
        )
    return MappingProxyType(items)


def load_item_catalog(root: Path = ASSET_ROOT / "items") -> ItemCatalog:
    """Read the prebuilt sprites without Pillow or a runtime network request."""
    data = object_fields(
        load_json(root / "items.json"),
        ("version", "foods", "weapons"),
        optional=("readables",),
        context="items",
    )
    if type(data["version"]) is not int or data.get("version") not in (1, 2):
        raise ValueError("Unsupported item catalog version")
    foods = _items(root, data.get("foods"), food=True)
    weapons = _items(root, data.get("weapons"), food=False)
    if set(foods) != set(DEFAULT_CATALOG.menu_order):
        raise ValueError("Food assets and nutrition menu must have the same IDs")
    if set(foods).intersection(weapons):
        raise ValueError("Item IDs must be unique across categories")
    return ItemCatalog(foods, weapons, _readables(data.get("readables", [])))


def _readables(records: object) -> Mapping[str, ReadableItem]:
    if not isinstance(records, list):
        raise ValueError("Invalid readable asset list")
    result: dict[str, ReadableItem] = {}
    for value in records:
        row = object_fields(
            value, ("id", "label_key", "state_manifest"), context="readable"
        )
        if any(not isinstance(row[k], str) for k in row):
            raise ValueError("Invalid readable metadata")
        path = (ASSET_ROOT / row["state_manifest"]).resolve()
        if not path.is_relative_to(ASSET_ROOT.resolve()):
            raise ValueError("Readable manifest escapes assets")
        data = load_json(path)
        if (
            not isinstance(data, dict)
            or data.get("version") != 1
            or set(data.get("states", {}))
            != {"closed_world", "carry_closed", "half_open", "open_reading"}
        ):
            raise ValueError("Invalid readable state manifest")
        states: dict[str, Mapping[int, ItemSprite]] = {}
        for name, state in data["states"].items():
            variants: dict[int, ItemSprite] = {}
            for scale in (1, 2):
                spec = state["variants"][str(scale)]
                image, size = _png(path.parent, spec["path"])
                display, display_size = _png(path.parent, spec["display_path"])
                pivot = spec["pivot"]
                if (
                    size != display_size
                    or list(size) != spec["size"]
                    or len(pivot) != 2
                    or any(type(v) not in (int, float) for v in pivot)
                    or not 0 <= pivot[0] <= size[0]
                    or not 0 <= pivot[1] <= size[1]
                ):
                    raise ValueError("Invalid readable geometry")
                variants[scale] = ItemSprite(
                    image, (float(pivot[0]), float(pivot[1])), display
                )
            states[name] = MappingProxyType(variants)
        icon = _png(path.parent, data["icons"]["32"])[0]
        key = row["id"]
        if not key.isidentifier() or key in result:
            raise ValueError("Invalid or duplicate readable id")
        offset = data.get("held_registration", {}).get("attachment_offset_1x", [0, 0])
        if (
            not isinstance(offset, list)
            or len(offset) != 2
            or any(
                type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 96
                for v in offset
            )
        ):
            raise ValueError("Invalid readable hand attachment")
        world_zoom = data.get("world_registration", {}).get("zoom", 1)
        if type(world_zoom) is not int or not 1 <= world_zoom <= 3:
            raise ValueError("Invalid readable World size")
        result[key] = ReadableItem(
            key,
            GERMAN_TEXT.format(row["label_key"]),
            icon,
            MappingProxyType(states),
            (float(offset[0]), float(offset[1])),
            world_zoom,
        )
    return MappingProxyType(result)
