"""Passive game-owned image overlays; no World objects or rule state."""

from __future__ import annotations

import math
import sys
import time
import tkinter as tk
from collections.abc import Callable
from pathlib import Path


class GameEffects:
    def __init__(
        self, owner: tk.Toplevel, *, topmost: bool,
        configure: Callable[[tk.Toplevel], None],
    ) -> None:
        self.owner, self._topmost, self._configure = owner, topmost, configure
        self._windows: dict[str, tuple[tk.Toplevel, tk.Label]] = {}
        self._images: dict[tuple[Path, int], tk.PhotoImage] = {}
        self._frames: dict[str, tuple[tk.PhotoImage, str]] = {}
        self._visible: set[str] = set()
        self._controls: set[str] = set()
        self._captions: dict[str, str] = {}
        self._timers: list[str] = []
        self._generation = 0
        self._closed = False

    def image(self, path: Path, width: int) -> tk.PhotoImage:
        key = path, width
        if key not in self._images:
            source = tk.PhotoImage(master=self.owner, file=str(path))
            divisor = math.gcd(source.width(), width)
            self._images[key] = source.zoom(width // divisor).subsample(
                source.width() // divisor,
            )
        return self._images[key]

    def show(self, name: str, image: tk.PhotoImage, x: float, y: float) -> None:
        if self._closed:
            return
        created = name not in self._windows
        if created:
            window = tk.Toplevel(self.owner)
            window.withdraw()
            window.overrideredirect(True)
            background = '#ff00ff' if sys.platform == 'win32' else '#202733'
            window.configure(bg=background)
            window.wm_attributes('-topmost', self._topmost)
            if sys.platform == 'win32':
                window.wm_attributes('-toolwindow', True)
                window.wm_attributes('-transparentcolor', '#ff00ff')
            label = tk.Label(window, bd=0, bg=background)
            label.pack()
            self._windows[name] = window, label
        window, label = self._windows[name]
        geometry = f'{image.width()}x{image.height()}+{round(x)}+{round(y)}'
        previous = self._frames.get(name)
        if previous is None or previous[0] is not image:
            label.configure(image=image)
        if previous is None or previous[1] != geometry:
            window.geometry(geometry)
        self._frames[name] = image, geometry
        if created:
            self._configure(window)
        if name not in self._visible:
            window.deiconify()
            self._visible.add(name)

    def caption(self, name: str, text: str) -> None:
        if self._captions.get(name) == text:
            return
        self._captions[name] = text
        self._windows[name][1].configure(
            text=text, compound="center", fg="#776093", font=("Segoe UI", 10, "bold"),
        )

    def control(
        self, name: str, configure: Callable[[tk.Toplevel], None],
        action: Callable[[], None],
    ) -> None:
        if name not in self._controls:
            window, label = self._windows[name]
            configure(window)
            label.configure(cursor="hand2")
            label.bind("<ButtonPress-1>", lambda _: action())
            self._controls.add(name)

    def hide(self, name: str) -> None:
        if name in self._windows:
            self._windows[name][0].withdraw()
            self._visible.discard(name)

    def later(self, ms: int, action: Callable[[], None]) -> None:
        generation = self._generation
        token = ''

        def run() -> None:
            if token in self._timers:
                self._timers.remove(token)
            if not self._closed and generation == self._generation:
                action()
        token = self.owner.after(ms, run)
        self._timers.append(token)

    def tween(
        self, ms: int, draw: Callable[[float], None], done: Callable[[], None],
    ) -> None:
        start = time.monotonic()

        def frame() -> None:
            fraction = min(1.0, (time.monotonic() - start) * 1000 / ms)
            draw(fraction)
            if fraction >= 1:
                done()
            else:
                self.later(16, frame)
        frame()

    def cancel(self) -> None:
        self._generation += 1
        for timer in self._timers:
            self.owner.after_cancel(timer)
        self._timers.clear()
        for window, _label in self._windows.values():
            window.withdraw()
        self._visible.clear()

    def set_topmost(self, enabled: bool) -> None:
        self._topmost = enabled
        for window, _label in self._windows.values():
            window.wm_attributes('-topmost', enabled)

    def close(self) -> None:
        self.cancel()
        self._closed = True
        for window, _label in self._windows.values():
            window.destroy()
        self._windows.clear()
        self._images.clear()
        self._frames.clear()
        self._controls.clear()
        self._captions.clear()
