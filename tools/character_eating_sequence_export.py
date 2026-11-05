"""Bake a reviewed private interpolation bank into an optional HD meal pack.

The legacy atlas files, gaze and locomotion assets are untouched; both display
sizes reuse this approved sequence, with 1x derived from its HD images in memory.
Interpolation dependencies and full-resolution originals stay outside Git.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PIL import Image

from aiko_pet.infrastructure.eating_assets import load_hd_eating_clip
from tools.character_export_common import sha256_digest

# The existing gesture is reused for each bite; the return trip also uses the
# same interpolated pairs in reverse. Never jump from chewing straight to mouth.
MEAL_PATH = (
    "00", "00a", "01", "01a", "02", "02a", "03", "04", "05",
    "04", "03", "02a", "02", "02a", "03", "04", "05",
    "04", "03", "02a", "02", "02a", "03", "04", "05",
    "05a", "06", "06a", "07",
)
BITE_POSITIONS = frozenset((6, 14, 22))
HOLDS = {
    "00": 200, "00a": 100, "01": 140, "01a": 100, "02": 160,
    "02a": 80, "03": 140, "04": 280, "05": 260, "05a": 140,
    "06": 220, "06a": 120, "07": 400,
}


def prepare_meal(bank: dict[str, Any]) -> list[dict[str, Any]]:
    """Build three bite cycles and linearly interpolate the held-item anchor."""
    sources = {row["id"]: row for row in bank["sources"]}
    pairs = {(row["from"], row["to"]): row["frames"]
             for row in bank["transitions"]}
    result: list[dict[str, Any]] = []

    def add(row: dict[str, Any], duration: int, anchor: list[int] | None,
            events: list[str]) -> None:
        name = Path(row["file"]).stem.lower()
        if re.fullmatch(r"[a-z0-9_-]+", name) is None:
            raise ValueError("Unsafe interpolation frame name")
        result.append({"file": f"actions/eat/{name}.png",
                       "duration_ms": duration, "sha256": row["sha256"],
                       "food_anchor": [round(n / 2) for n in anchor]
                       if anchor is not None else None, "events": events,
                       "private_file": row["file"]})

    for index, key in enumerate(MEAL_PATH):
        source = sources[key]
        visible = index < 22
        anchor = source["food_anchor_2x_world"] if visible else None
        add(source, HOLDS[key], anchor,
            ["bite"] if index in BITE_POSITIONS else [])
        if index == len(MEAL_PATH) - 1:
            continue
        next_key = MEAL_PATH[index + 1]
        pair = pairs.get((key, next_key))
        reverse = pair is None
        if reverse:
            pair = pairs.get((next_key, key))
        if pair is None or len(pair) != 2:
            raise ValueError(f"Missing reviewed interpolations: {key}->{next_key}")
        first, last = (source["food_anchor_2x_world"],
                       sources[next_key]["food_anchor_2x_world"])
        for row in reversed(pair) if reverse else pair:
            t = 1 - row["t"] if reverse else row["t"]
            # No overlay after bite three. Null endpoint07 is already hidden.
            between = ([round(a + (b - a) * t) for a, b in zip(first, last)]
                       if visible and first is not None and last is not None
                       else None)
            add(row, 40, between, [])
    return result


def export_meal(source_job: Path, asset_root: Path) -> dict[str, Any]:
    bank = json.loads((source_job / "bank.json").read_text("utf-8"))
    if bank["size"] != [384, 416] or bank["world_floor_y"] != 388:
        raise ValueError("Expected world-registered HD interpolation bank")
    rows = prepare_meal(bank)
    manifest = {"version": 1, "size": [384, 416], "anchor": [96, 194],
                "frames": [{k: v for k, v in row.items() if k != "private_file"}
                           for row in rows]}
    with TemporaryDirectory(prefix="meal-stage-", dir=asset_root.parent) as folder:
        staging = Path(folder)
        copied: dict[str, str] = {}
        for row in rows:
            source = (source_job / row["private_file"]).resolve()
            if not source.is_relative_to(source_job.resolve()):
                raise ValueError("Interpolation path escapes its private job")
            payload = source.read_bytes()
            if sha256_digest(payload) != row["sha256"]:
                raise ValueError("Interpolation source hash mismatch")
            with Image.open(source) as image:
                if image.mode != "RGBA" or image.size != (384, 416):
                    raise ValueError("Expected a prepared HD RGBA sprite")
                if set(image.getchannel("A").tobytes()) != {0, 255}:
                    raise ValueError("Expected clean binary-alpha export")
            relative = row["file"]
            if relative in copied:
                if copied[relative] != row["sha256"]:
                    raise ValueError("Conflicting interpolation frame names")
                continue
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            copied[relative] = row["sha256"]
        (staging / "actions/eat.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf-8",
        )
        load_hd_eating_clip(staging)
        for relative in [*copied, "actions/eat.json"]:
            target = asset_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging / relative, target)
    return {"playback_frames": len(rows), "unique_images": len(copied),
            "duration_ms": sum(row["duration_ms"] for row in rows),
            "bites": 3, "legacy_atlas_unchanged": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_job", type=Path)
    parser.add_argument("asset_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(export_meal(args.source_job, args.asset_root)))


if __name__ == "__main__":
    main()
