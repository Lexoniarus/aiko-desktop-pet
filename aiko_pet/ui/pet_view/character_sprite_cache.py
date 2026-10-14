"""Cache immutable character PNGs and lazily zoom only visible 2x poses.

Tk PhotoImage operations must stay on Tk's owner thread.  A scale toggle
does not need to re-read all 112 PNGs or enlarge all of them synchronously.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Sequence
from pathlib import Path
from typing import overload

from ...pet.animation.character import CharacterCatalog, FRAME_HEIGHT, FRAME_WIDTH


class _ScaledFrames(Sequence[tk.PhotoImage]):
    """One clip; each 2x frame is zoomed at most once when actually shown."""

    def __init__(
        self, originals: tuple[tk.PhotoImage, ...], *, scale: int,
        zoomed: dict[str, tk.PhotoImage],
    ) -> None:
        self._originals = originals
        self._scale = scale
        self._zoomed = zoomed

    def __len__(self) -> int:
        return len(self._originals)

    @overload
    def __getitem__(self, index: int) -> tk.PhotoImage: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[tk.PhotoImage]: ...

    def __getitem__(
        self, index: int | slice,
    ) -> tk.PhotoImage | Sequence[tk.PhotoImage]:
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        if not -len(self) <= index < len(self):
            raise IndexError(index)
        index %= len(self)
        original = self._originals[index]
        if self._scale == 1:
            return original
        key = str(original)
        image = self._zoomed.get(key)
        if image is None:
            image = original.zoom(2)
            self._zoomed[key] = image
        return image


class CharacterSpriteCache:
    """Own 112 original images plus persistent per-scale render views."""

    def __init__(self, root: tk.Tk, catalog: CharacterCatalog) -> None:
        originals: dict[str, tuple[tk.PhotoImage, ...]] = {}
        by_path: dict[Path, tk.PhotoImage] = {}
        for state, clip in catalog.clips.items():
            loaded: list[tk.PhotoImage] = []
            for definition in clip.frames:
                path = definition.file
                frame = by_path.get(path)
                if frame is None:
                    if not path.is_file():
                        raise FileNotFoundError(f"Missing sprite: {path}")
                    frame = tk.PhotoImage(master=root, file=str(path))
                    if (frame.width(), frame.height()) != (
                        FRAME_WIDTH, FRAME_HEIGHT,
                    ):
                        raise ValueError(f"Invalid sprite dimensions: {path}")
                    by_path[path] = frame
                loaded.append(frame)
            originals[state] = tuple(loaded)
        self._originals = originals
        self._shared_zoomed: dict[str, tk.PhotoImage] = {}
        self._views: dict[int, dict[str, Sequence[tk.PhotoImage]]] = {}

    def for_scale(self, scale: int) -> dict[str, Sequence[tk.PhotoImage]]:
        if scale not in (1, 2):
            raise ValueError("Character scale must be 1 or 2")
        if scale not in self._views:
            self._views[scale] = {
                name: _ScaledFrames(
                    frames, scale=scale, zoomed=self._shared_zoomed,
                )
                for name, frames in self._originals.items()
            }
        return self._views[scale]
