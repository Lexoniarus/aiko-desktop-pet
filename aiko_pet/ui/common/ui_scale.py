"""One immutable 4K design-to-display transform for the entire Tk application."""

from __future__ import annotations

import base64
import io
import tkinter as tk
from dataclasses import dataclass
from tkinter import font as tkfont
from typing import Any
from weakref import WeakKeyDictionary


@dataclass(frozen=True, slots=True)
class DisplayScale:
    """Coordinates already use Tk's screen space, including OS DPI virtualization."""

    factor: float

    @classmethod
    def for_resolution(cls, width: int, height: int) -> DisplayScale:
        if width <= 0 or height <= 0:
            raise ValueError("Display dimensions must be positive")
        return cls(min(1.0, width / 3840, height / 2160))

    def pixels(self, value: float) -> int:
        return round(value * self.factor)

    def logical(self, value: float) -> float:
        return value / self.factor


class UiScale:
    """Shared fonts and filtered UI images; never measures or resizes a form."""

    _roots: WeakKeyDictionary[tk.Misc, UiScale] = WeakKeyDictionary()

    @classmethod
    def for_widget(cls, widget: tk.Misc) -> UiScale:
        root = widget
        while root.master is not None:
            root = root.master
        if root not in cls._roots:
            cls._roots[root] = cls(root, DisplayScale.for_resolution(
                root.winfo_screenwidth(), root.winfo_screenheight(),
            ))
        return cls._roots[root]

    def __init__(self, root: tk.Misc, display: DisplayScale) -> None:
        self.root, self.display = root, display
        self._images: dict[str, tk.PhotoImage] = {}
        self._fonts: dict[str, tkfont.Font] = {}
        root.bind("<Destroy>", self._destroyed, add="+")

    @property
    def factor(self) -> float:
        return self.display.factor

    def pixels(self, value: float) -> int:
        return self.display.pixels(value)

    def logical(self, value: float) -> float:
        return self.display.logical(value)

    def distance(self, value: Any) -> Any:
        parts = (value,) if isinstance(value, (int, float)) else (
            getattr(self.root.tk, "splitlist")(value)
        )
        result = tuple(self.pixels(self.root.winfo_fpixels(v)) for v in parts)
        return result[0] if len(result) == 1 else result

    def font(self, value: Any) -> str:
        key = str(value)
        if key not in self._fonts:
            font = tkfont.Font(root=self.root, font=value)
            size = font.actual("size")
            # Negative pixel fonts avoid applying Tk's DPI multiplier a second
            # time. Positive design sizes are points at the 96-DPI design grid.
            pixels = size * 96 / 72 if size > 0 else abs(size)
            font.configure(size=-max(1, self.pixels(pixels)))
            self._fonts[key] = font
        return str(self._fonts[key])

    def image(self, value: Any) -> str:
        from PIL import Image

        name = str(value)
        if not name or self.factor == 1:
            return name
        if name not in self._images:
            data = self.root.tk.call(name, "data", "-format", "png")
            if isinstance(data, str):
                data = base64.b64decode(data)
            with Image.open(io.BytesIO(data)) as source:
                size = (max(1, self.pixels(source.width)),
                        max(1, self.pixels(source.height)))
                resized = source.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                encoded = io.BytesIO()
                resized.save(encoded, format="PNG")
            self._images[name] = tk.PhotoImage(
                master=self.root, data=encoded.getvalue(),
            )
        return str(self._images[name])

    def image_list(self, value: Any) -> tuple[Any, ...]:
        parts = getattr(self.root.tk, "splitlist")(str(value))
        # Native ttk image specifications alternate image and optional states.
        names = set(getattr(self.root.tk, "splitlist")(
            self.root.tk.call("image", "names"),
        ))
        return tuple(self.image(v) if str(v) in names else v for v in parts)

    def _destroyed(self, event: tk.Event) -> None:
        if event.widget is self.root:
            self._images.clear()
            self._fonts.clear()
            self._roots.pop(self.root, None)
