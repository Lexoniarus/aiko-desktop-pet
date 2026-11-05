"""Register private V3 eating originals and replace only their 2x export.

Original PNGs remain outside Git. This offline tool preserves uniform source
proportions, the existing eating floor/contact contracts and every 1x asset.
Run after the legacy archive export when rebuilding the complete character.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from tools.character_export_common import (
    BINARY_ALPHA_TABLE,
    HD_FRAME_SIZE,
    sha256_digest,
)

FLOOR = 392
FOOT_CENTER = 192
VISIBLE_HEIGHT = 312


def register_pose(source: Image.Image) -> tuple[Image.Image, dict[str, object]]:
    """Scale both axes together and register the shoe center and floor."""
    rgba = source.convert("RGBA")
    mask = rgba.getchannel("A").point(BINARY_ALPHA_TABLE)
    bounds = mask.getbbox()
    if bounds is None:
        raise ValueError("Empty eating source")
    left, top, right, bottom = bounds
    width, height = right - left, bottom - top
    # The lowest 14% covers the planted shoes without using the asymmetric hair
    # outline to infer a foot anchor. All eight poses use the same rule.
    shoe_top = bottom - max(1, round(height * 0.14))
    shoes = mask.crop((left, shoe_top, right, bottom)).getbbox()
    if shoes is None:
        raise ValueError("Eating source has no visible feet")
    source_foot_center = (shoes[0] + shoes[2]) / 2
    scale = VISIBLE_HEIGHT / height
    target_width = round(width * scale)
    if target_width <= 0 or target_width > HD_FRAME_SIZE[0]:
        raise ValueError("Eating source cannot fit without changing proportions")
    placed = rgba.crop(bounds).resize(
        (target_width, VISIBLE_HEIGHT), Image.Resampling.LANCZOS,
    )
    x = round(FOOT_CENTER - source_foot_center * target_width / width)
    y = FLOOR - VISIBLE_HEIGHT
    if x < 0 or x + target_width > HD_FRAME_SIZE[0]:
        raise ValueError("Registered eating sprite would be clipped")
    output = Image.new("RGBA", HD_FRAME_SIZE)
    output.alpha_composite(placed, dest=(x, y))
    output.putalpha(output.getchannel("A").point(BINARY_ALPHA_TABLE))
    return output, {
        "source_bbox": list(bounds),
        "uniform_scale": scale,
        "aspect_rescale_ratio": (target_width / width) / scale,
        "registration_origin": [x, y],
        "foot_anchor_2x": [FOOT_CENTER, FLOOR],
        "reference_frame": "idle/00.png",
        "visible_height": VISIBLE_HEIGHT,
    }


def export_eating(originals: Path, hd_root: Path) -> list[dict[str, object]]:
    """Validate and stage all eight images before replacing any live file."""
    manifest_path = hd_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != 1 or manifest.get("size") != list(HD_FRAME_SIZE):
        raise ValueError("Expected the current 384x416 character manifest")
    records = manifest["frames"]
    expected = {f"eat/{number:02}.png" for number in range(8)}
    existing = [record["path"] for record in records]
    if len(existing) != len(set(existing)) or not expected.issubset(existing):
        raise ValueError("Manifest must contain every eating frame exactly once")
    prepared: list[tuple[str, Image.Image, dict[str, object]]] = []
    source_digests: dict[str, str] = {}
    for number in range(1, 9):
        source_path = originals / f"{number:02}.png"
        payload = source_path.read_bytes()
        with Image.open(source_path) as source:
            if min(source.size) < 1000 or source.mode != "RGBA":
                raise ValueError(f"Expected a large RGBA original: {source_path}")
            if source.getchannel("A").getextrema()[0] != 0:
                raise ValueError(f"Expected genuine transparency: {source_path}")
            image, registration = register_pose(source)
        relative = f"eat/{number - 1:02}.png"
        source_digest = sha256_digest(payload)
        record: dict[str, object] = {
            "path": relative,
            "source": f"private-v3-eating/{number:02}.png",
            "status": "generated_v3_eating_individual_original",
            "source_sha256": source_digest,
            **registration,
        }
        if source_digest in source_digests:
            record["status"] = "reused_v3_eating_individual_original"
            record["reused_from_frame"] = source_digests[source_digest]
        else:
            source_digests[source_digest] = relative
        prepared.append((relative, image, record))
    with TemporaryDirectory(prefix="eating-v3-", dir=hd_root.parent) as folder:
        staging = Path(folder)
        replacements: dict[str, dict[str, object]] = {}
        for relative, image, record in prepared:
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            image.save(target, optimize=True)
            record["sha256"] = sha256_digest(target.read_bytes())
            record["bytes"] = target.stat().st_size
            replacements[relative] = record
        manifest["frames"] = [
            replacements.get(record["path"], record) for record in records
        ]
        staged_manifest = staging / "manifest.json"
        staged_manifest.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        for relative, _image, _record in prepared:
            os.replace(staging / relative, hd_root / relative)
        os.replace(staged_manifest, manifest_path)
    return list(replacements.values())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("originals", type=Path)
    parser.add_argument("--hd-root", type=Path, required=True)
    args = parser.parse_args()
    records = export_eating(args.originals, args.hd_root)
    print(json.dumps({"exported": len(records), "frames": records}, indent=2))


if __name__ == "__main__":
    main()
