"""Composite an eight-phase blanket cycle over a stationary HD sleeping pose."""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi
from typing import cast

from PIL import Image, ImageDraw

SIZE = (384, 416)
ALPHA = [255 if value >= 128 else 0 for value in range(256)]


@dataclass(frozen=True)
class SleepCycle:
    """Registered images and their measurable blanket contours."""

    frames: tuple[Image.Image, ...]
    contours: tuple[tuple[tuple[int, int, int], ...], ...]
    factors: tuple[float, ...]
    mask: Image.Image


def _blanket_bounds(image: Image.Image, x: int) -> tuple[int, int]:
    rows = []
    for y in range(248 if x < 247 else 230, 316):
        r, g, b, alpha = cast(tuple[int, int, int, int], image.getpixel((x, y)))
        if alpha >= 128 and b > r * 1.25 and b > g * 1.6 and b > 45:
            rows.append(y)
    if not rows:
        raise ValueError(f"Missing blue blanket column at {x}")
    return max(226, min(rows) - 3), min(314, max(rows) + 2)


def _ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def build_sleep_cycle(rest: Image.Image, raised: Image.Image) -> SleepCycle:
    """Use two registered originals, retaining the rest pose outside the blanket.

    The shoulder and bed joins ease to zero displacement. An eight-sample cosine
    then interpolates the blanket contour and texture between rest and peak;
    head, hands, pillow and bed always come from the same rest image.
    Coordinates describe this approved Aiko export, not a general segmentation.
    """
    if rest.size != SIZE or raised.size != SIZE:
        raise ValueError("Sleep anchors must be registered at 384 by 416")
    rest, raised = rest.convert("RGBA"), raised.convert("RGBA")
    peak = rest.copy()
    mask = Image.new("L", SIZE)
    draw = ImageDraw.Draw(mask)
    anchors = []
    for x in range(237, 346):
        weight = _ease((x - 236) / 24) * _ease((346 - x) / 16)
        bt, bottom = _blanket_bounds(rest, x)
        dt, db = _blanket_bounds(raised, x)
        top = round(bt + weight * (dt - bt))
        size = (1, bottom - top)
        a = rest.crop((x, bt, x + 1, bottom)).resize(size, Image.Resampling.LANCZOS)
        b = raised.crop((x, dt, x + 1, db)).resize(size, Image.Resampling.LANCZOS)
        clear_top = max(0, min(top, bt) - 3)
        peak.paste((0, 0, 0, 0), (x, clear_top, x + 1, bottom))
        peak.paste(Image.blend(a, b, weight), (x, top))
        draw.line((x, clear_top, x, bottom - 1), fill=255)
        anchors.append((x, bt, top, bottom))
    peak.putalpha(peak.getchannel("A").point(ALPHA))
    factors = tuple(round((1 - cos(2 * pi * i / 8)) / 2, 12) for i in range(8))
    frames = []
    contours = []
    for index, factor in enumerate(factors):
        frame = rest.copy()
        points = []
        for x, bt, pt, bottom in anchors:
            top = round(bt + factor * (pt - bt))
            size = (1, bottom - top)
            a = rest.crop((x, bt, x + 1, bottom)).resize(
                size, Image.Resampling.LANCZOS,
            )
            b = peak.crop((x, pt, x + 1, bottom)).resize(
                size, Image.Resampling.LANCZOS,
            )
            frame.paste((0, 0, 0, 0), (x, max(0, min(top, bt) - 3), x + 1, bottom))
            frame.paste(Image.blend(a, b, factor), (x, top))
            points.append((x, top, bottom))
        frame.putalpha(frame.getchannel("A").point(ALPHA))
        frame = Image.composite(frame, rest, mask)
        if index == 0:
            frame = rest.copy()
        elif index == 4:
            frame = peak.copy()
        frames.append(frame)
        contours.append(tuple(points))
    return SleepCycle(tuple(frames), tuple(contours), factors, mask)
