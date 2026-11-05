"""Image contracts shared by offline character exporters, never runtime code."""

from __future__ import annotations

import hashlib
import io

from PIL import Image

HD_FRAME_SIZE = (384, 416)
BINARY_ALPHA_TABLE = [255 if value >= 128 else 0 for value in range(256)]
Box = tuple[int, int, int, int]


def sha256_digest(payload: bytes) -> str:
    """Fingerprint the exact reviewed source or published PNG bytes."""
    return hashlib.sha256(payload).hexdigest()


def load_rgba_component(payload: bytes) -> Image.Image:
    """Decode a reviewed HD component, retaining its original pixel values."""
    with Image.open(io.BytesIO(payload)) as image:
        if image.mode != "RGBA" or image.size != HD_FRAME_SIZE:
            raise ValueError("Expected a reviewed 384x416 RGBA component")
        result: Image.Image = image.copy()
        return result


def planted_foot_bounds(image: Image.Image) -> Box:
    """Locate planted shoes in the lowest twelve percent of a figure."""
    mask = image.getchannel("A").point(BINARY_ALPHA_TABLE)
    bounds = mask.getbbox()
    if bounds is None:
        raise ValueError("Empty character pose")
    left, top, right, bottom = bounds
    shoe_top = bottom - max(1, round((bottom - top) * 0.12))
    shoes = mask.crop((left, shoe_top, right, bottom)).getbbox()
    if shoes is None:
        raise ValueError("Character pose has no planted shoes")
    return (left + shoes[0], shoe_top + shoes[1],
            left + shoes[2], shoe_top + shoes[3])
