"""Derive color-key-compatible item copies; original artwork stays untouched."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.pet.catalog_validation import load_json

ALPHA_THRESHOLD = 128


def prepare(root: Path = ASSET_ROOT / "items") -> None:
    manifest = root / "items.json"
    data = load_json(manifest)
    records: list[dict[str, Any]] = []
    for item in data["foods"]:
        for scale, variant in item["variants"].items():
            source = (root / variant["path"]).resolve()
            if not source.is_relative_to(root.resolve()):
                raise ValueError("Item source escapes its asset directory")
            relative = f"display/{scale}x/{item['id']}.png"
            target = (root / relative).resolve()
            if not target.is_relative_to((root / "display").resolve()):
                raise ValueError("Item display path escapes its asset directory")
            if target == source:
                raise ValueError("Display preparation must not overwrite its source")
            with Image.open(source) as raw:
                image = raw.convert("RGBA")
            image.putalpha(image.getchannel("A").point(
                [255 if alpha >= ALPHA_THRESHOLD else 0 for alpha in range(256)],
            ))
            if image.getbbox() is None:
                raise ValueError(f"Empty item display image: {source.name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            image.save(target, optimize=True)
            variant["display_path"] = relative
            records.append({
                "source": variant["path"], "display": relative,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "display_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "size": list(image.size), "pivot": variant["pivot"],
            })
    for path, value in (
        (manifest, data),
        (root / "display/provenance.json", {
            "version": 1, "alpha_threshold": ALPHA_THRESHOLD,
            "preparation": "Binary alpha for Windows color-key display; RGB unchanged",
            "license": "../LICENSE.md", "files": records,
        }),
    ):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")


if __name__ == "__main__":
    prepare()
