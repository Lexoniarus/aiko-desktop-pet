"""Root-local packaged VN image cache; no domain state or worker-thread Tk."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

from ...asset_paths import ASSET_ROOT
from ...pet.catalog_validation import load_json
from .button_styles import ButtonStyles


class IconImages:
    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._directory = ASSET_ROOT / "ui"
        self._catalog = load_json(self._directory / "catalog.json")
        self._images: dict[str, tk.PhotoImage] = {}
        self._released = False
        self._buttons: ButtonStyles | None = None
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

    def panel_art(self, width: int, height: int) -> tk.PhotoImage:
        """Keep rounded source corners; tile quiet center strips with native Tk.

        The view owns this size-specific image, avoiding an unbounded resize cache.
        No runtime Pillow dependency or changes to the source artwork are needed.
        """
        source = self.surface("panel_surface.panel")
        width, height = max(1, width), max(1, height)
        cap = min(12, width // 2, height // 2)
        sw, sh = source.width(), source.height()
        sx = (0, cap, sw - cap, sw)
        sy = (0, cap, sh - cap, sh)
        dx, dy = (0, cap, width - cap, width), (0, cap, height - cap, height)
        result = tk.PhotoImage(master=self._root, width=width, height=height)
        for row in range(3):
            for col in range(3):
                if dx[col + 1] <= dx[col] or dy[row + 1] <= dy[row]:
                    continue
                # One quiet center row/column extends without repeating gradients.
                left = sw // 2 if col == 1 else sx[col]
                top = sh // 2 if row == 1 else sy[row]
                right = left + 1 if col == 1 else sx[col + 1]
                bottom = top + 1 if row == 1 else sy[row + 1]
                result.tk.call(
                    str(result), "copy", str(source),
                    "-from", left, top, right, bottom,
                    "-to", dx[col], dy[row], dx[col + 1], dy[row + 1],
                )
        return result

    @property
    def buttons(self) -> ButtonStyles:
        if self._released:
            raise RuntimeError("UI images have been released")
        if self._buttons is None:
            self._buttons = ButtonStyles(self._root, self.surface)
        return self._buttons

    def file(self, path: Path, size: int = 32) -> tk.PhotoImage:
        """Existing item/card image, shared by all menu/wish consumers."""
        if self._released:
            raise RuntimeError("UI images have been released")
        key = f"{path.resolve()}:{size}"
        if key not in self._images:
            image = tk.PhotoImage(master=self._root, file=str(path))
            factor = max(1, (max(image.width(), image.height()) + size - 1) // size)
            content = image.subsample(factor) if factor > 1 else image
            canvas = tk.PhotoImage(master=self._root, width=size, height=size)
            canvas.tk.call(
                str(canvas), "copy", str(content), "-to",
                (size - content.width()) // 2, (size - content.height()) // 2,
            )
            self._images[key] = canvas
        return self._images[key]

    def _destroyed(self, event: tk.Event) -> None:
        if event.widget is self._root:
            self.release()

    def release(self) -> None:
        self._buttons = None
        self._images.clear()
        self._released = True
