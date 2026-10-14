"""Prepare small hand/menu food PNGs without modifying source artwork.

Developer-only: python tools/prepare_food_assets.py --source DIR
Requires Pillow (not an Aiko Desktop Pet runtime dependency).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

RUNTIME_SIZE_PIXELS = 64
SOURCE_OBJECT_EDGE_PIXELS = 61
HELD_FOOD_SCALE = 0.98  # Exactly 2% smaller than the design target.
PALETTE_COLORS = 64

SOURCE_NAMES = {
    "onigiri": "Glänzendes Onigiri mit Noriwickel.png",
    "sandwich": "Dreieckiges Sandwich mit Ei und Salat.png",
    "taiyaki": "Goldbraunes Taiyaki als Sticker.png",
    "apple": "Glänzender roter Apfel mit Blatt.png",
    "dango": "Glänzender Hanami-Dango-Spieß.png",
}


def prepare_food(source: Path, output: Path) -> None:
    """Preserve aspect, transparent borders and a centered bottom pivot."""
    with Image.open(source) as raw:
        image = raw.convert("RGBA")
    solid = image.getchannel("A").point(
        [255 if alpha >= 24 else 0 for alpha in range(256)],
    )
    bounds = solid.getbbox()
    if bounds is None:
        raise ValueError(f"Food image is entirely transparent: {source}")
    cropped = image.crop(bounds)
    target_edge = SOURCE_OBJECT_EDGE_PIXELS * HELD_FOOD_SCALE
    factor = min(
        target_edge / cropped.width, target_edge / cropped.height,
    )
    size = (
        max(1, round(cropped.width * factor)),
        max(1, round(cropped.height * factor)),
    )
    scaled = cropped.resize(size, Image.Resampling.LANCZOS)
    sheet = Image.new(
        "RGBA", (RUNTIME_SIZE_PIXELS, RUNTIME_SIZE_PIXELS),
    )
    sheet.alpha_composite(
        scaled, ((RUNTIME_SIZE_PIXELS - size[0]) // 2,
                 RUNTIME_SIZE_PIXELS - 1 - size[1]),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.quantize(
        colors=PALETTE_COLORS,
        method=Image.Quantize.FASTOCTREE,
        dither=Image.Dither.NONE,
    ).save(output, optimize=True, compress_level=9)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, required=True,
        help="Directory with the original transparent, high-res food PNGs",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path(__file__).resolve().parents[1]
        / "aiko_pet" / "assets" / "food",
    )
    args = parser.parse_args()
    for food_id, filename in SOURCE_NAMES.items():
        src = args.source / filename
        if not src.is_file():
            raise FileNotFoundError(src)
        dst = args.output / f"{food_id}.png"
        prepare_food(src, dst)
        print(f"Prepared {dst}")


if __name__ == "__main__":
    main()
