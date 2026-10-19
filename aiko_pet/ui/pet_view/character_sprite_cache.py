"""Cache 1x sprites and lazily load true-HD 2x originals when provisioned.

Every 1x frame remains the established 192x208 PNG. The optional, complete
384x416 HD export comes from matching owner-licensed source artwork. Its
metadata is validated once; images are only decoded on demand in the Tk thread.
"""

from __future__ import annotations

import json
import re
import tkinter as tk
from collections.abc import Sequence
from pathlib import Path
from typing import overload

from ...pet.animation.character import FRAME_HEIGHT, FRAME_WIDTH, CharacterCatalog


class _ScaledFrames(Sequence[tk.PhotoImage]):
    """One clip, lazily loading each genuine 2x asset at most once."""

    def __init__(
        self, originals: tuple[tk.PhotoImage, ...], *, scale: int,
        zoomed: dict[str, tk.PhotoImage],
        hd_paths: dict[str, Path], root: tk.Tk,
    ) -> None:
        self._originals = originals
        self._hd_paths = hd_paths
        self._root = root
        self._scale = scale
        self._zoomed = zoomed
        self._hd_paths = hd_paths
        self._root = root
        self._hd_paths = hd_paths
        self._root = root

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
            hd = self._hd_paths.get(key)
            if hd is not None:
                image = tk.PhotoImage(master=self._root, file=str(hd))
                if (image.width(), image.height()) != (
                    FRAME_WIDTH * 2, FRAME_HEIGHT * 2,
                ):
                    raise ValueError(f"Unexpected 2x sprite dimensions: {hd}")
            else:
                # Backward compatibility with older/partial installs.
                image = original.zoom(2)
            self._zoomed[key] = image
        return image


def _hd_assets_by_original(
    loaded: dict[Path, tk.PhotoImage],
) -> dict[str, Path]:
    """Either validate the complete HD export or preserve legacy zooming."""
    if not loaded:
        return {}
    roots = {path.parent.parent for path in loaded}
    if len(roots) != 1:
        return {}
    native_root = next(iter(roots))
    if native_root.name != "frames":
        return {}
    hd_root = native_root.parent / "frames_2x"
    manifest_path = hd_root / "manifest.json"
    if not manifest_path.is_file():
        return {}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1 or data.get(
        "size",
    ) != [FRAME_WIDTH * 2, FRAME_HEIGHT * 2]:
        raise ValueError("Invalid 2x asset manifest version or dimensions")
    records = data.get("frames")
    if not isinstance(records, list):
        raise ValueError("Invalid 2x frame records")
    wanted = {path.relative_to(native_root).as_posix() for path in loaded}
    found: dict[str, Path] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Invalid 2x frame record")
        relative = record.get("path")
        sha = record.get("sha256")
        if (not isinstance(relative, str)
                or not re.fullmatch(r"[A-Za-z0-9_-]+/[0-9]{2}\.png", relative)
                or not isinstance(sha, str)
                or not re.fullmatch(r"[a-f0-9]{64}", sha)
                or relative in found):
            raise ValueError("Invalid or duplicate 2x frame path/digest")
        candidate = (hd_root / relative).resolve()
        if not candidate.is_relative_to(hd_root.resolve()) or not candidate.is_file():
            raise FileNotFoundError(f"Missing 2x character frame: {candidate}")
        found[relative] = candidate
    if set(found) != wanted:
        raise ValueError("2x frames do not match the active character catalogue")
    return {str(image): found[path.relative_to(native_root).as_posix()]
            for path, image in loaded.items()}


class CharacterSpriteCache:
    """Own native images and one persistent cache for visible 2x variants."""

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
        self._hd_paths = _hd_assets_by_original(by_path)
        self._shared_zoomed: dict[str, tk.PhotoImage] = {}
        self._views: dict[int, dict[str, Sequence[tk.PhotoImage]]] = {}
        self._root = root

    def for_scale(self, scale: int) -> dict[str, Sequence[tk.PhotoImage]]:
        if scale not in (1, 2):
            raise ValueError("Character scale must be 1 or 2")
        if scale not in self._views:
            self._views[scale] = {
                name: _ScaledFrames(
                    frames, scale=scale, zoomed=self._shared_zoomed,
                    hd_paths=self._hd_paths, root=self._root,
                )
                for name, frames in self._originals.items()
            }
        return self._views[scale]

    def close(self) -> None:
        """Release the Tk image owners before tearing down the window."""
        for view in self._views.values():
            view.clear()
        self._views.clear()
        self._shared_zoomed.clear()
        self._hd_paths.clear()
        self._originals.clear()
