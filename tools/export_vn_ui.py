"""Deterministic development-only VN exports; original masters stay untouched."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "ui-vn" / "v1"
DEST = ROOT / "aiko_pet" / "assets" / "ui"
SIZES = {
    "small": (40, 40),
    "regular": (180, 44),
    "wide": (280, 44),
    "action": (246, 50),
    "footer": (306, 40),
}


def optical_crop(image: Image.Image) -> Image.Image:
    bounds = image.getchannel("A").point([0] * 8 + [255] * 248).getbbox()
    if bounds is None:
        raise ValueError("Empty UI source")
    return image.crop(bounds)


def nine_slice(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Preserve cap proportions; scale only quiet edges/center between caps."""
    width, height = size
    # Normalize border thickness to the target height before slicing corners.
    scale = height / image.height
    image = image.resize(
        (max(height * 2, round(image.width * scale)), height), Image.Resampling.LANCZOS
    )
    cap = min(height // 3, width // 3)
    source_x = (0, cap, image.width - cap, image.width)
    source_y = (0, cap, height - cap, height)
    dest_x = (0, cap, width - cap, width)
    dest_y = (0, cap, height - cap, height)
    result = Image.new("RGBA", size)
    for row in range(3):
        for col in range(3):
            piece = image.crop((
                source_x[col],
                source_y[row],
                source_x[col + 1],
                source_y[row + 1],
            ))
            piece = piece.resize(
                (dest_x[col + 1] - dest_x[col], dest_y[row + 1] - dest_y[row]),
                Image.Resampling.LANCZOS,
            )
            result.paste(piece, (dest_x[col], dest_y[row]))
    return result


def export() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    icons: dict[str, dict[str, str]] = {}
    surfaces: dict[str, str] = {}
    sources: dict[str, str] = {}
    for path in sorted((SOURCE / "icons").glob("*.png")):
        sources[path.relative_to(ROOT).as_posix()] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        with Image.open(path) as source:
            cropped = optical_crop(source.convert("RGBA"))
        variants = {}
        for size in (24, 32, 40, 48, 64, 96, 128):
            content = cropped.copy()
            content.thumbnail(
                (round(size * 0.9), round(size * 0.9)), Image.Resampling.LANCZOS
            )
            image = Image.new("RGBA", (size, size))
            image.paste(
                content, ((size - content.width) // 2, (size - content.height) // 2)
            )
            name = f"{path.stem}_{size}.png"
            image.save(DEST / name, optimize=True)
            variants[str(size)] = name
        icons[path.stem] = variants
    for path in sorted((SOURCE / "controls").glob("*.png")):
        sources[path.relative_to(ROOT).as_posix()] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        with Image.open(path) as source:
            image = optical_crop(source.convert("RGBA"))
        variants_to_export = (
            SIZES
            if path.stem.startswith("button_")
            else {"176": (176, 12), "280": (280, 12)}
            if path.stem.startswith("status_")
            else {"panel": (300, 160)}
        )
        for name, target_size in variants_to_export.items():
            filename = f"{path.stem}_{name}.png"
            nine_slice(image, target_size).save(DEST / filename, optimize=True)
            surfaces[f"{path.stem}.{name}"] = filename
    manifest = {
        "version": 1,
        "icons": icons,
        "surfaces": surfaces,
        "source_sha256": sources,
    }
    (DEST / "catalog.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    export()
