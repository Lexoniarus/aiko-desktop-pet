"""Separate native gaze poses and register them by their planted feet."""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from statistics import median
from typing import Any

from PIL import Image, ImageChops, ImageFilter

Box = tuple[int, int, int, int]
SIZE = (384, 416)
ALPHA = [255 if value >= 128 else 0 for value in range(256)]


def left_gaze_scale_adjustment(direction: int) -> float:
    """Ease a measured 2.3% left-pose size correction out toward down gaze.

    Up-left and left share the correction; down-left blends into the unchanged
    down pose. Scaling stays proportional and is applied before foot anchoring.
    """
    if not 0 <= direction < 16:
        raise ValueError("Expected a gaze direction from zero to fifteen")
    blend = min(1.0, max(0.0, (direction - 8) / 4))
    return 1.0 + 0.023 * blend * blend * (3 - 2 * blend)


def gaze_foot_offset_x(direction: int) -> int:
    """Balance two inherited lateral foot jumps with one-pixel translations."""
    if not 0 <= direction < 16:
        raise ValueError("Expected a gaze direction from zero to fifteen")
    return {10: -1, 11: 1, 14: 1, 15: -1}.get(direction, 0)


def _bounds(image: Image.Image) -> Box:
    bounds = image.getchannel("A").point(ALPHA).getbbox()
    if bounds is None:
        raise ValueError("Empty gaze pose")
    return bounds


def _feet(image: Image.Image) -> Box:
    left, top, right, bottom = _bounds(image)
    band_top = bottom - max(1, round((bottom - top) * 0.12))
    bounds = (
        image.getchannel("A")
        .point(ALPHA)
        .crop(
            (left, band_top, right, bottom),
        )
        .getbbox()
    )
    if bounds is None:
        raise ValueError("Gaze pose has no planted feet")
    return (
        left + bounds[0],
        band_top + bounds[1],
        left + bounds[2],
        band_top + bounds[3],
    )


@dataclass(frozen=True)
class GazePose:
    """One isolated pose, retaining original RGB and antialiased edges."""

    image: Image.Image
    source_crop: Box


def extract_gaze_poses(image: Image.Image, count: int = 8) -> list[GazePose]:
    """Separate connected figures even when their hair crosses equal cells.

    Alpha below eight contains bridges/noise in the native row-ten artwork.
    Grow each substantial component by two pixels to retain its original edge
    alpha, without including a neighboring figure in a rectangular crop.
    """
    image = image.convert("RGBA")
    width, height = image.size
    pending = bytearray(
        image.getchannel("A")
        .point(
            [255 if value >= 8 else 0 for value in range(256)],
        )
        .tobytes()
    )
    components: list[list[int]] = []
    minimum_area = max(16, width * height // 1000)
    for seed in range(len(pending)):
        if not pending[seed]:
            continue
        pending[seed] = 0
        queue = deque([seed])
        pixels: list[int] = []
        while queue:
            position = queue.popleft()
            pixels.append(position)
            x, y = position % width, position // width
            neighbors = (
                position - width if y else -1,
                position + width if y + 1 < height else -1,
                position - 1 if x else -1,
                position + 1 if x + 1 < width else -1,
            )
            for neighbor in neighbors:
                if neighbor >= 0 and pending[neighbor]:
                    pending[neighbor] = 0
                    queue.append(neighbor)
        if len(pixels) >= minimum_area:
            components.append(pixels)
    if len(components) != count:
        raise ValueError(f"Expected {count} separate gaze poses, got {len(components)}")
    components.sort(key=lambda pixels: min(position % width for position in pixels))
    poses: list[GazePose] = []
    for pixels in components:
        left = max(0, min(position % width for position in pixels) - 2)
        top = max(0, min(position // width for position in pixels) - 2)
        right = min(width, max(position % width for position in pixels) + 3)
        bottom = min(height, max(position // width for position in pixels) + 3)
        crop = image.crop((left, top, right, bottom))
        mask_bytes = bytearray(crop.width * crop.height)
        for position in pixels:
            x, y = position % width - left, position // width - top
            mask_bytes[y * crop.width + x] = 255
        mask = Image.frombytes("L", crop.size, bytes(mask_bytes)).filter(
            ImageFilter.MaxFilter(5),
        )
        crop.putalpha(ImageChops.multiply(crop.getchannel("A"), mask))
        poses.append(GazePose(crop, (left, top, right, bottom)))
    return poses


def register_gaze_row(
    image: Image.Image,
    references: list[Image.Image],
    *,
    scale_adjustments: Sequence[float] | None = None,
    horizontal_offsets: Sequence[int] | None = None,
) -> list[tuple[Image.Image, dict[str, Any]]]:
    """Use proportional row scaling, optional pose tuning and foot anchors."""
    if not references or any(reference.size != (192, 208) for reference in references):
        raise ValueError("Gaze references must be 192x208")
    adjustments = (
        list(scale_adjustments)
        if scale_adjustments is not None
        else [1.0] * len(references)
    )
    if len(adjustments) != len(references) or any(
        not isfinite(value) or value <= 0 for value in adjustments
    ):
        raise ValueError("Expected one positive finite scale adjustment per gaze pose")
    offsets = (
        list(horizontal_offsets)
        if horizontal_offsets is not None
        else [0] * len(references)
    )
    if len(offsets) != len(references):
        raise ValueError("Expected one horizontal offset per gaze pose")
    poses = extract_gaze_poses(image, len(references))
    source_feet = [_feet(pose.image) for pose in poses]
    target_feet = [_feet(reference) for reference in references]
    scale = (
        2
        * median(box[2] - box[0] for box in target_feet)
        / median(box[2] - box[0] for box in source_feet)
    )
    results: list[tuple[Image.Image, dict[str, Any]]] = []
    for pose, reference, source_foot, target_foot, adjustment, offset_x in zip(
        poses,
        references,
        source_feet,
        target_feet,
        adjustments,
        offsets,
        strict=True,
    ):
        source = pose.image
        effective_scale = scale * adjustment
        size = (
            round(source.width * effective_scale),
            round(source.height * effective_scale),
        )
        resized = source.resize(size, Image.Resampling.LANCZOS)
        resized.putalpha(resized.getchannel("A").point(ALPHA))
        resized_foot = _feet(resized)
        reference_x = target_foot[0] + target_foot[2]
        target_x = reference_x + offset_x
        target_y = 2 * target_foot[3]
        # Apply integer translation after rounding: half-pixel banker's rounding
        # before an odd offset would otherwise turn a one-pixel move into 0/2.
        x = round(reference_x - (resized_foot[0] + resized_foot[2]) / 2) + offset_x
        y = target_y - resized_foot[3]
        bounds = _bounds(resized)
        if (
            x + bounds[0] < 0
            or y + bounds[1] < 0
            or x + bounds[2] > SIZE[0]
            or y + bounds[3] > SIZE[1]
        ):
            raise ValueError("Registered gaze pose would be clipped")
        output = Image.new("RGBA", SIZE)
        output.alpha_composite(resized, (x, y))
        rendered_foot = _feet(output)
        reduced = output.getchannel("A").resize((192, 208), Image.Resampling.LANCZOS)
        reference_mask = reference.getchannel("A").point(ALPHA).tobytes()
        output_mask = reduced.tobytes()
        intersection = sum(
            a >= 128 and b >= 128
            for a, b in zip(
                reference_mask,
                output_mask,
                strict=True,
            )
        )
        union = sum(
            a >= 128 or b >= 128
            for a, b in zip(
                reference_mask,
                output_mask,
                strict=True,
            )
        )
        sx, sy = size[0] / source.width, size[1] / source.height
        rendered_x = (rendered_foot[0] + rendered_foot[2]) / 2
        results.append((
            output,
            {
                "source_bbox": list(_bounds(source)),
                "reference_bbox": list(_bounds(reference)),
                "aspect_rescale_ratio": round(sx / sy, 4),
                "silhouette_iou": round(intersection / union, 4),
                "source_crop": list(pose.source_crop),
                "registration": "uniform_row_scale_foot_anchor",
                "row_scale": scale,
                **(
                    {
                        "horizontal_anchor_adjustment": offset_x,
                        "reference_foot_anchor": [reference_x, target_y],
                    }
                    if offset_x
                    else {}
                ),
                **(
                    {
                        "scale_adjustment": adjustment,
                        "effective_scale": effective_scale,
                    }
                    if adjustment != 1.0
                    else {}
                ),
                "source_foot_anchor": [
                    (source_foot[0] + source_foot[2]) / 2,
                    source_foot[3],
                ],
                "target_foot_anchor": [target_x, target_y],
                "rendered_foot_anchor": [rendered_x, rendered_foot[3]],
                "foot_anchor_error": [
                    rendered_x - target_x,
                    rendered_foot[3] - target_y,
                ],
            },
        ))
    return results
