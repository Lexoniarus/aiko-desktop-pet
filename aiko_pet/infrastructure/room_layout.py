"""Load the one versioned layout shared by Python and the room renderer."""

from __future__ import annotations

import json
import math
from functools import cache
from pathlib import Path
from typing import Any

from ..asset_paths import ASSET_ROOT
from ..world.room_layout import FurniturePlacement, RoomLayout, RoomWall


@cache
def load_room_layout(path: Path = ASSET_ROOT / "room/v1/layout.json") -> RoomLayout:
    raw: dict[str, Any] = json.loads(path.read_text("utf8"))
    numbers = (
        "width",
        "depth",
        "wall_height",
        "cell_size",
        "pet_height",
        "pet_radius",
        "camera_height",
        "camera_clearance",
    )
    if raw["version"] != 2 or any(
        type(raw[key]) not in (int, float)
        or not math.isfinite(raw[key])
        or raw[key] <= 0
        for key in numbers
    ):
        raise ValueError("Invalid room dimensions")
    items = tuple(
        FurniturePlacement(
            item["id"],
            item["asset"],
            item["x"],
            item["z"],
            item["width"],
            item["depth"],
            item["height"],
            item.get("wall"),
            item.get("elevation", 0),
            item["blocking"],
            tuple(item["crop"]),
            tuple(item["pivot"]),
        )
        for item in raw["furniture"]
    )
    if len({item.id for item in items}) != len(items):
        raise ValueError("Duplicate room furniture")
    for item in items:
        if (
            not all(
                math.isfinite(v)
                for v in (
                    item.x,
                    item.z,
                    item.width,
                    item.depth,
                    item.height,
                    item.elevation,
                )
            )
            or min(item.width, item.height) <= 0
            or item.depth < 0
            or item.elevation < 0
            or item.wall
            not in (
                None,
                "north",
                "east",
                "south",
                "west",
            )
            or not 0 <= item.x <= raw["width"]
            or not 0 <= item.z <= raw["depth"]
            or len(item.crop) != 4
            or min(item.crop) < 0
            or len(item.pivot) != 2
            or not all(0 <= value <= 1 for value in item.pivot)
        ):
            raise ValueError("Invalid furniture placement")
    walls = tuple(RoomWall(wall["id"], wall["asset"]) for wall in raw["walls"])
    if len(walls) != 4 or {wall.id for wall in walls} != {
        "north",
        "east",
        "south",
        "west",
    }:
        raise ValueError("A room requires four distinct walls")
    return RoomLayout(
        raw["id"],
        raw["revision"],
        raw["width"],
        raw["depth"],
        raw["wall_height"],
        raw["cell_size"],
        raw["pet_height"],
        raw["pet_radius"],
        raw["camera_height"],
        raw["camera_clearance"],
        items,
        walls,
    )
