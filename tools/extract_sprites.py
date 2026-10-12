"""One-time asset preparation from the user's original exported sprite atlas.

Requires Pillow for DEVELOPMENT ONLY. Running the pet uses Python's standard library.
Example: python tools/extract_sprites.py path/to/Aiko_Pet_Arbeitsstand.zip
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

from PIL import Image

FRAME_WIDTH, FRAME_HEIGHT = 192, 208
CROP = (32, 0, 160, 208)
FRAME_COUNTS = {
    "idle": 6,
    "running-right": 8,
    "running-left": 8,
    "waving": 4,
    "jumping": 5,
    "failed": 8,
    "waiting": 6,
    "running": 6,
    "review": 6,
    "look": 16,
}


def extract(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        source = archive.read("final/spritesheet-extended.png")
    atlas = Image.open(io.BytesIO(source)).convert("RGBA")
    if atlas.size != (1536, 2288):
        raise ValueError(f"Unexpected atlas size: {atlas.size}")
    for row, (state, count) in enumerate(FRAME_COUNTS.items()):
        directory = dest / state
        directory.mkdir(parents=True, exist_ok=True)
        for i in range(count):
            atlas_row = 9 + i // 8 if state == "look" else row
            atlas_col = i % 8
            cell = atlas.crop(
                (atlas_col * FRAME_WIDTH, atlas_row * FRAME_HEIGHT,
                 (atlas_col + 1) * FRAME_WIDTH, (atlas_row + 1) * FRAME_HEIGHT)
            )
            cell = cell.crop(CROP)
            # Windows chroma-key transparency works best with 0/255 alpha.
            # Soft alpha edges on pixel-adjacent art would leave magenta halos.
            alpha = cell.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
            cell.putalpha(alpha)
            cell.save(directory / f"{i:02d}.png", optimize=True)

    manifest = {
        "source_asset": "Aiko_Pet_Arbeitsstand.zip / final/spritesheet-extended.png",
        "source_atlas_sha256": hashlib.sha256(source).hexdigest(),
        "frame_counts": FRAME_COUNTS,
        "crop_from_original_pixels": list(CROP),
        "size": [CROP[2] - CROP[0], CROP[3] - CROP[1]],
        "alpha_threshold": 128,
        "note": (
            "Sämtliche bestehenden Frames sind erhalten; "
            "es wurden keine neuen Posen generiert."
        ),
    }
    (dest.parent / "provenance.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Extracted {sum(FRAME_COUNTS.values())} frames into {dest}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python tools/extract_sprites.py ORIGINAL.zip")
    output = Path(__file__).resolve().parents[1] / "aiko_pet" / "assets" / "frames"
    extract(Path(sys.argv[1]), output)
