"""Make small pose-relative head/shoulder motion without new artwork.

The original flattened sprites have no independent head layer. For a rest
pose only, horizontal pixel rows are displaced gradually from the head
through the shoulders, returning to zero before the stationary feet.
Tk PhotoImage keeps the runtime free of Pillow and generated art assets.
"""

from __future__ import annotations

import tkinter as tk


class RestPoseRenderer:
    """Cache gentle source-pose warps; never alter the canonical sprites."""

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._variants: dict[tuple[str, int], tk.PhotoImage] = {}

    def clear(self) -> None:
        """Invalidate scaled variants after sprite assets are reloaded."""
        self._variants.clear()

    def resolve(
        self, original: tk.PhotoImage, *,
        offset: int, scale: int,
    ) -> tk.PhotoImage:
        """Move hair/head slightly while keeping leg and foot pixels fixed."""
        if not -2 <= offset <= 2:
            raise ValueError("A rest-pose offset must be within two pixels")
        if scale not in (1, 2):
            raise ValueError("Invalid sprite scale")
        if offset == 0:
            return original
        key = (str(original), offset)
        cached = self._variants.get(key)
        if cached is not None:
            return cached
        width, height = original.width(), original.height()
        if (width, height) != (192 * scale, 208 * scale):
            raise ValueError("Unexpected rest-pose sprite dimensions")

        warped = tk.PhotoImage(
            master=self._root, width=width, height=height,
        )
        head_end = 119 * scale
        taper_end = 174 * scale
        shift_px = offset * scale

        def shift_at(y: int) -> int:
            if y <= head_end:
                return shift_px
            if y >= taper_end:
                return 0
            return round(shift_px * (taper_end - y) / (taper_end - head_end))

        start_y = 0
        while start_y < height:
            dx = shift_at(start_y)
            end_y = start_y + 1
            while end_y < height and shift_at(end_y) == dx:
                end_y += 1
            # The source has a generous transparent border around Aiko.
            # Copy with clipped bounds so no invalid pixel coordinates occur.
            source_start = max(0, -dx)
            source_end = min(width, width - dx)
            if source_end > source_start:
                warped.tk.call(
                    str(warped), "copy", str(original),
                    "-from", source_start, start_y, source_end, end_y,
                    "-to", source_start + dx, start_y,
                )
            start_y = end_y
        self._variants[key] = warped
        return warped
