"""One live 4K design-to-display transform for the entire Tk application."""

from __future__ import annotations

import base64
import io
import tkinter as tk
from dataclasses import dataclass
from tkinter import font as tkfont
from typing import Any
from weakref import WeakKeyDictionary

from .display_metrics import virtualization_factor


@dataclass(frozen=True, slots=True)
class DisplayScale:
    """A single design-to-Tk factor; physical display detection happens at startup."""

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
                round(root.winfo_screenwidth() * virtualization_factor()),
                round(root.winfo_screenheight() * virtualization_factor()),
            ))
        return cls._roots[root]

    def __init__(self, root: tk.Misc, display: DisplayScale) -> None:
        self.root, self.display = root, display
        self._base = display.factor
        self.percent = 100
        self._images: dict[str, tk.PhotoImage] = {}
        self._sources: dict[str, bytes] = {}
        self._fonts: dict[str, tkfont.Font] = {}
        self._font_sizes: dict[str, float] = {}
        self._pending: str | None = None
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
            self._font_sizes[key] = pixels
        return str(self._fonts[key])

    def _image_data(self, name: str) -> bytes:
        from PIL import Image

        if name not in self._sources:
            data = self.root.tk.call(name, "data", "-format", "png")
            if isinstance(data, str):
                data = base64.b64decode(data)
            self._sources[name] = data
        data = self._sources[name]
        with Image.open(io.BytesIO(data)) as source:
            size = (max(1, self.pixels(source.width)),
                    max(1, self.pixels(source.height)))
            resized = source.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
            # Windows color-key windows cannot composite fractional alpha.
            # Binary source masks must remain binary after filtering, otherwise
            # Tk blends their edges with magenta and Windows leaves a fringe.
            histogram = source.convert("RGBA").getchannel("A").histogram()
            if not sum(histogram[1:255]):
                resized.putalpha(resized.getchannel("A").point(
                    [0] * 128 + [255] * 128,
                ))
            encoded = io.BytesIO()
            resized.save(encoded, format="PNG")
            return encoded.getvalue()

    def image(self, value: Any) -> str:
        name = str(value)
        if not name:
            return name
        if name not in self._images:
            self._images[name] = tk.PhotoImage(
                master=self.root, data=self._image_data(name),
            )
        return str(self._images[name])

    def set_percent(self, percent: int) -> None:
        """Rescale existing views in place; models, focus and timers survive."""
        if type(percent) is not int or percent not in (75, 100, 125, 150, 175, 200):
            raise ValueError("Unsupported UI size")
        if percent == self.percent:
            return
        previous = self.factor
        self.percent = percent
        self.display = DisplayScale(self._base * percent / 100)
        for key, font in self._fonts.items():
            font.configure(size=-max(1, self.pixels(self._font_sizes[key])))
        for source, painted in self._images.items():
            painted.configure(data=self._image_data(source))

        def visit(widget: tk.Misc) -> None:
            rescale = getattr(widget, "_rescale", None)
            if rescale is not None:
                rescale(self.factor / previous)
            if isinstance(widget, tk.Toplevel):
                width, height = widget.minsize()
                widget.minsize(round(width * self.factor / previous),
                               round(height * self.factor / previous))
            for child in widget.winfo_children():
                visit(child)
        visit(self.root)
        if self._pending is not None:
            self.root.after_cancel(self._pending)
        self._pending = self.root.after_idle(self._settled)

    def _settled(self) -> None:
        self._pending = None
        self.root.event_generate("<<UiScaleChanged>>")
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel) and widget.winfo_ismapped():
                x = max(0, min(widget.winfo_x(),
                               self.root.winfo_screenwidth()
                               - widget.winfo_reqwidth()))
                y = max(0, min(widget.winfo_y(),
                               self.root.winfo_screenheight()
                               - widget.winfo_reqheight()))
                widget.geometry(f"+{x}+{y}")

    def image_list(self, value: Any) -> tuple[Any, ...]:
        parts = getattr(self.root.tk, "splitlist")(str(value))
        # Native ttk image specifications alternate image and optional states.
        names = set(getattr(self.root.tk, "splitlist")(
            self.root.tk.call("image", "names"),
        ))
        return tuple(self.image(v) if str(v) in names else v for v in parts)

    def _destroyed(self, event: tk.Event) -> None:
        if event.widget is self.root:
            if self._pending is not None:
                self.root.after_cancel(self._pending)
                self._pending = None
            self._images.clear()
            self._sources.clear()
            self._fonts.clear()
            self._roots.pop(self.root, None)
