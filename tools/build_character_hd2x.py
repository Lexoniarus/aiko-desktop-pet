"""Export real-resolution 2x pickup sprites without upscaling runtime pixels.

Usage:
    python -m tools.build_character_hd2x "Aiko_Pick_Up_und_Hinlegen.zip"

The approved ZIP is a local owner-provided source and is not stored in the
public repository. This pilot prepares only the eight pickup poses. It does
not generate new poses or silently claim other clips have approved HD art.
"""

from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

from PIL import Image

from aiko_pet.asset_paths import ASSET_ROOT

SIZE_1X = (192, 208)
SIZE_2X = (384, 416)
ALPHA_THRESHOLD = [255 if a >= 128 else 0 for a in range(256)]


def compose_registered(
    high_resolution: Image.Image,
    approved_1x: Image.Image,
) -> Image.Image:
    """Map an HD pose onto the approved 1x silhouette footprint at 2x."""
    source = high_resolution.convert("RGBA")
    native = approved_1x.convert("RGBA")
    if native.size != SIZE_1X:
        raise ValueError("Expected 192x208 pickup source geometry")
    source_bounds = source.getchannel("A").getbbox()
    native_bounds = native.getchannel("A").getbbox()
    if source_bounds is None or native_bounds is None:
        raise ValueError("Empty pickup source frame")
    target = tuple(coordinate * 2 for coordinate in native_bounds)
    width, height = target[2] - target[0], target[3] - target[1]
    resized = source.crop(source_bounds).resize(
        (width, height), Image.Resampling.LANCZOS,
    )
    resized.putalpha(resized.getchannel("A").point(ALPHA_THRESHOLD))
    output = Image.new("RGBA", SIZE_2X)
    output.paste(resized, target[:2])
    return output


def prepare_pickup(
    archive: Path,
    destination: Path = ASSET_ROOT / "frames_2x" / "pick_up",
) -> tuple[Path, ...]:
    """Validate all eight high-resolution sources before publishing frames."""
    outputs: list[Image.Image] = []
    with zipfile.ZipFile(archive) as bundle:
        for number in range(1, 9):
            high = f"Registriert_Hochaufloesend/{number:02}.png"
            native = f"Laufzeit_192x208/{number:02}.png"
            with Image.open(io.BytesIO(bundle.read(high))) as img:
                if img.width < SIZE_2X[0] or img.height < SIZE_2X[1]:
                    raise ValueError(f"Source is not genuinely HD: {high}")
                original = img.convert("RGBA")
            with Image.open(io.BytesIO(bundle.read(native))) as img:
                approved = img.convert("RGBA")
            outputs.append(compose_registered(original, approved))
    destination.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i, image in enumerate(outputs):
        path = destination / f"{i:02}.png"
        image.save(path, optimize=True)
        paths.append(path)
    return tuple(paths)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Approved Aiko pickup ZIP")
    parser.add_argument(
        "--output", type=Path, default=ASSET_ROOT / "frames_2x" / "pick_up",
        help="Output folder for eight 384x416 character PNGs",
    )
    args = parser.parse_args()
    result = prepare_pickup(args.archive, args.output)
    print(f"Prepared {len(result)} real-source pickup frames at 384x416.")


if __name__ == "__main__":
    main()
