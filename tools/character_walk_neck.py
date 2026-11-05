"""Fit existing neck pixels to a walking collar without moving the head."""

from __future__ import annotations

from typing import cast

from PIL import Image

from tools.character_neck_join_export import NECK_BOUNDS


def rgba_pixel(image: Image.Image, point: tuple[int, int]) -> tuple[int, ...]:
    """Read a pixel after the caller has validated the RGBA image mode."""
    return cast(tuple[int, ...], image.getpixel(point))


def _skin(pixel: tuple[int, ...]) -> bool:
    red, green, blue, alpha = pixel
    return (alpha >= 128 and red >= 135 and green >= 70 and blue >= 40
            and red > green + 7 and green > blue + 2)


def fit_walk_neck(
    current: Image.Image, head: Image.Image, body: Image.Image, *,
    anchor: int, side: str,
) -> Image.Image:
    """Keep the jaw, fit only its lower neck, and retain clothing in front.

    Inputs are existing, registered RGBA components at 384x416. ``anchor`` is
    the first neck row below the approved jaw, including its existing gait
    bob. The collar's actual upper contour determines the lower attachment.
    Texture comes from the same head's skin rows, never another head/pose.
    """
    if side not in ("left", "right") or not 233 <= anchor <= 247:
        raise ValueError("Expected a registered walk neck below its jaw")
    if any(im.mode != "RGBA" or im.size != (384, 416)
           for im in (current, head, body)):
        raise ValueError("Expected registered 384x416 RGBA walk components")
    middle = 186 if side == "right" else 200

    def samples(y: int) -> list[int]:
        return [x for x in range(middle - 9, middle + 10)
                if _skin(rgba_pixel(head, (x, y)))]

    rows = [(y, samples(y)) for y in range(anchor, 256)]
    rows = [(y, xs) for y, xs in rows if xs]
    if not rows or rows[0][0] != anchor:
        raise ValueError("No source neck at the approved jaw boundary")
    first = rows[0][1]
    collar = [y for y in range(232, 254) for x in range(165, 221)
              if rgba_pixel(body, (x, y))[3] >= 128]
    if not collar:
        raise ValueError("No collar at the registered walk attachment")
    bottom = max(anchor + 3, min(collar) + 6)
    edge = [x for x in range(165, 221)
            if rgba_pixel(body, (x, bottom))[3] >= 128]
    if bottom >= NECK_BOUNDS[3] - 1 or not edge:
        raise ValueError("Walking collar escapes the reviewed neck bounds")
    width = first[-1] - first[0]
    end = ((max(edge) - width, max(edge)) if side == "right"
           else (min(edge), min(edge) + width))
    foreground = head.copy()
    # Remove the old hanging skin cut and its adjacent dark side edge.
    for y in range(anchor, NECK_BOUNDS[3]):
        for x in range(165, 231):
            pixel = rgba_pixel(head, (x, y))
            red, green, blue, alpha = pixel
            lateral = any(_skin(rgba_pixel(head, (xx, y))) for xx in (x - 1, x + 1))
            if _skin(pixel) or (alpha >= 128 and lateral and red < 150
                                and green <= red + 12 and blue <= red + 25):
                foreground.putpixel((x, y), (0, 0, 0, 0))
    _remove_cut_strokes(foreground, anchor)
    neck = Image.new("RGBA", current.size)
    for y in range(anchor, bottom + 2):
        fraction = min(1.0, (y - anchor) / (bottom - anchor))
        left = round(first[0] + fraction * (end[0] - first[0]))
        right = round(first[-1] + fraction * (end[1] - first[-1]))
        source_y, xs = rows[round(fraction * (len(rows) - 1))]
        for x in range(left, right + 1):
            source_x = xs[0] + (x - left) * (xs[-1] - xs[0]) / max(1, right - left)
            nearest = min(xs, key=lambda value: abs(value - source_x))
            neck.putpixel((x, y), rgba_pixel(head, (nearest, source_y)))
    fitted = Image.alpha_composite(neck, foreground)
    fitted.alpha_composite(body)
    result = current.copy()
    # Jaw and head above the attachment remain exactly the installed pixels.
    bounds = (NECK_BOUNDS[0], anchor, NECK_BOUNDS[2], NECK_BOUNDS[3])
    result.paste(fitted.crop(bounds), bounds[:2])
    for y in range(anchor, NECK_BOUNDS[3]):
        for x in range(165, 231):
            pixel = rgba_pixel(result, (x, y))
            if pixel[3] < 128:
                old = rgba_pixel(current, (x, y))
                result.putpixel((x, y), old if old[3] == 0 else (0, 0, 0, 0))
            else:
                result.putpixel((x, y), (*pixel[:3], 255))
    return result


def _remove_cut_strokes(head: Image.Image, anchor: int) -> None:
    """Drop only tiny detached dark garment strokes inside the lower join."""
    seen: set[tuple[int, int]] = set()
    for y in range(anchor, 259):
        for x in range(165, 231):
            if (x, y) in seen or rgba_pixel(head, (x, y))[3] < 128:
                continue
            group, stack = {(x, y)}, [(x, y)]
            seen.add((x, y))
            escapes = False
            while stack:
                xx, yy = stack.pop()
                if not (165 <= xx < 231 and anchor <= yy < 259):
                    escapes = True
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    point = xx + dx, yy + dy
                    if (point in seen or not 0 <= point[0] < 384
                            or not 0 <= point[1] < 416):
                        continue
                    if rgba_pixel(head, point)[3] >= 128:
                        seen.add(point)
                        group.add(point)
                        stack.append(point)
            if (not escapes and len(group) <= 12
                    and all(max(rgba_pixel(head, p)[:3]) < 130 for p in group)):
                for point in group:
                    head.putpixel(point, (0, 0, 0, 0))
