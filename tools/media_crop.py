"""Capture native-size, fully visible Tk interfaces with tight framing.

This developer-only Pillow utility captures the whole virtual screen first,
then crops to the union of the *actual mapped Tk windows* with safe padding.
It never guesses a fixed rectangle that can cut off the toolbar or a bubble.
Animated captures share one crop rectangle for every frame, avoiding jumps.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageChops, ImageGrab

Box = tuple[int, int, int, int]
PADDING = 24


def framed_bounds(
    windows: Sequence[Box], screen_size: tuple[int, int], *,
    padding: int = PADDING,
) -> Box:
    """Return the smallest safe box covering every actual window.

    A requested window may never be partially outside the physical capture.
    A margin on each side provides a visual breathing space and ensures that
    a clipped window is not silently published as a complete screenshot.
    """
    width, height = screen_size
    if not windows or width < 1 or height < 1 or padding < 0:
        raise ValueError("Missing windows, invalid screen or crop padding")
    for left, top, right, bottom in windows:
        if (
            right <= left or bottom <= top
            or left < padding or top < padding
            or right > width - padding or bottom > height - padding
        ):
            raise ValueError(
                "A visible Tk window would be cut off by the screen edge: "
                f"{(left, top, right, bottom)} on {screen_size}"
            )
    return (
        min(box[0] for box in windows) - padding,
        min(box[1] for box in windows) - padding,
        max(box[2] for box in windows) + padding,
        max(box[3] for box in windows) + padding,
    )


@dataclass(frozen=True, slots=True)
class CapturedFrame:
    """A complete monitor image and its actual mapped application windows."""

    desktop: Image.Image
    window_boxes: tuple[Box, ...]

    @property
    def crop_box(self) -> Box:
        return framed_bounds(self.window_boxes, self.desktop.size)

    def cropped(self, box: Box | None = None) -> Image.Image:
        """Return raw screen pixels at their native scale, without resizing."""
        chosen = self.crop_box if box is None else box
        left, top, right, bottom = chosen
        if (
            left < 0 or top < 0
            or right > self.desktop.width or bottom > self.desktop.height
            or right <= left or bottom <= top
        ):
            raise ValueError("Crop rectangle is outside the captured desktop")
        if any(
            win[0] < left or win[1] < top
            or win[2] > right or win[3] > bottom
            for win in self.window_boxes
        ):
            raise ValueError("The crop would cut off an application window")
        return self.desktop.crop(chosen)

    def save_png(self, path: Path) -> None:
        image = self.cropped()
        if ImageChops.difference(
            image, Image.new("RGB", image.size, (0, 0, 0)),
        ).getbbox() is None:
            raise RuntimeError("The captured Tk screenshot is empty")
        image.save(path, optimize=True)


def capture_screen(root: tk.Tk) -> CapturedFrame:
    """Capture every mapped child Toplevel, including character and bubbles."""
    root.update_idletasks()
    if not root.winfo_ismapped():
        raise RuntimeError("The character window is not mapped")
    width, height = root.winfo_screenwidth(), root.winfo_screenheight()
    windows: list[Box] = []
    for widget in (root, *(
        child for child in root.winfo_children()
        if isinstance(child, tk.Toplevel)
    )):
        if not widget.winfo_ismapped():
            continue
        x, y = widget.winfo_rootx(), widget.winfo_rooty()
        w, h = widget.winfo_width(), widget.winfo_height()
        windows.append((x, y, x + w, y + h))
    # Check geometries before a costly screen grab and again when cropping.
    framed_bounds(windows, (width, height))
    screen: Image.Image = ImageGrab.grab(
        bbox=(0, 0, width, height),
    ).convert("RGB")
    if screen.size != (width, height):
        raise RuntimeError("The desktop capture has unexpected dimensions")
    return CapturedFrame(screen, tuple(windows))


def save_sequence(
    frames: Sequence[CapturedFrame], durations_ms: Sequence[int],
    path: Path,
) -> None:
    """Use a single union crop for a stable, correctly framed animated GIF."""
    if not frames or len(frames) != len(durations_ms):
        raise ValueError("GIF frames and frame durations must match")
    screen_size = frames[0].desktop.size
    if any(frame.desktop.size != screen_size for frame in frames):
        raise ValueError("All animation frames need one desktop size")
    if any(duration <= 0 for duration in durations_ms):
        raise ValueError("Invalid GIF frame duration")
    bounds = framed_bounds(
        [box for frame in frames for box in frame.window_boxes],
        screen_size,
    )
    cropped = [frame.cropped(bounds) for frame in frames]
    cropped[0].save(
        path, save_all=True, append_images=cropped[1:],
        duration=list(durations_ms), loop=0, disposal=2,
        optimize=True,
    )
