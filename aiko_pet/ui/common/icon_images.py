"""Root-local packaged VN image cache; no domain state or worker-thread Tk."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

from ...asset_paths import ASSET_ROOT
from ...pet.catalog_validation import load_json


class IconImages:
    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._directory = ASSET_ROOT / "ui"
        self._catalog = load_json(self._directory / "catalog.json")
        self._images: dict[str, tk.PhotoImage] = {}
        self._released = False
        root.bind("<Destroy>", self._destroyed, add="+")

    def _load(self, filename: str) -> tk.PhotoImage:
        if self._released:
            raise RuntimeError("UI images have been released")
        path = self._directory / filename
        if path.parent != self._directory or path.suffix != ".png":
            raise ValueError("Invalid packaged UI path")
        if filename not in self._images:
            self._images[filename] = tk.PhotoImage(master=self._root, file=str(path))
        return self._images[filename]

    def icon(self, key: str, size: int = 32) -> tk.PhotoImage:
        return self._load(self._catalog["icons"][key][str(size)])

    def surface(self, key: str) -> tk.PhotoImage:
        return self._load(self._catalog["surfaces"][key])

    def button_art(
        self, state: str, size: str, icon: tk.PhotoImage | None
    ) -> tk.PhotoImage:
        base = self.surface(f"button_{state}.{size}")
        if icon is None:
            return base
        key = f"button:{state}:{size}:{icon}"
        if key not in self._images:
            combined = base.copy()
            combined.tk.call(
                str(combined),
                "copy",
                str(icon),
                "-to",
                8,
                max(0, (base.height() - icon.height()) // 2),
            )
            self._images[key] = combined
        return self._images[key]

    def file(self, path: Path, size: int = 32) -> tk.PhotoImage:
        """Existing item/card image, shared by all menu/wish consumers."""
        if self._released:
            raise RuntimeError("UI images have been released")
        key = f"{path.resolve()}:{size}"
        if key not in self._images:
            image = tk.PhotoImage(master=self._root, file=str(path))
            factor = max(1, (max(image.width(), image.height()) + size - 1) // size)
            self._images[key] = image.subsample(factor) if factor > 1 else image
        return self._images[key]

    def _destroyed(self, event: tk.Event) -> None:
        if event.widget is self._root:
            self.release()

    def release(self) -> None:
        self._images.clear()
        self._released = True
