"""Lazy baked body frames: original 2x images and downsampled 1x views."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Sequence
from pathlib import Path
from typing import overload

from ...pet.animation.character import CharacterCatalog


class _BodyFrames(Sequence[tk.PhotoImage]):
    def __init__(
        self, files: tuple[Path, ...], cache: BodyPoseCache, scale: int,
    ) -> None:
        self._files = files
        self._cache = cache
        self._scale = scale

    def __len__(self) -> int:
        return len(self._files)

    @overload
    def __getitem__(self, index: int) -> tk.PhotoImage: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[tk.PhotoImage]: ...

    def __getitem__(
        self, index: int | slice,
    ) -> tk.PhotoImage | Sequence[tk.PhotoImage]:
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        return self._cache.image(self._files[index], self._scale)


class BodyPoseCache:
    """Keep optional poses separate from unchanged legacy 1x/2x assets."""

    def __init__(self, root: tk.Tk, catalog: CharacterCatalog) -> None:
        self._root = root
        self._clips = {**catalog.body_clips, **catalog.expression_clips}
        self._images: dict[tuple[Path, int], tk.PhotoImage] = {}

    def image(self, path: Path, scale: int) -> tk.PhotoImage:
        key = path, scale
        if key not in self._images:
            if scale == 1:
                image = self.image(path, 2).subsample(2)
            elif scale == 2:
                image = tk.PhotoImage(master=self._root, file=str(path))
                if (image.width(), image.height()) != (384, 416):
                    raise ValueError(f"Unexpected body pose dimensions: {path}")
            else:
                raise ValueError("Invalid body pose scale")
            self._images[key] = image
        return self._images[key]

    def for_scale(self, scale: int) -> dict[str, Sequence[tk.PhotoImage]]:
        if scale not in (1, 2):
            raise ValueError("Invalid body pose scale")
        return {
            name: _BodyFrames(tuple(f.file for f in clip.frames), self, scale)
            for name, clip in self._clips.items()
        }

    def close(self) -> None:
        self.clear()

    def clear(self) -> None:
        """Reload updated baked PNGs when the sprite view is refreshed."""
        self._images.clear()
