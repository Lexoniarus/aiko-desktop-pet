"""One anchored safe, public code lights and cancellable illustrated opening."""

from __future__ import annotations

import math
import sys
import tkinter as tk
from collections.abc import Callable

from ...asset_paths import GAME_ART_DIR
from ..common.mastermind_images import MastermindImages
from ..common.window_geometry import WindowBounds
from ..view_models.game_models import HandAnchor
from ..view_models.mastermind_models import CodeView


class MastermindSafePresenter:
    def __init__(
        self, root: tk.Tk, *, images: MastermindImages,
        anchor: Callable[[], HandAnchor], topmost: Callable[[], bool],
        configure_window: Callable[[tk.Toplevel], None],
        restore_stack: Callable[[], object],
        occupied: Callable[[], tuple[WindowBounds, ...]],
    ) -> None:
        self._root, self._anchor = root, anchor
        self._topmost, self._configure = topmost, configure_window
        self._restore_stack = restore_stack
        self.window: tk.Toplevel | None = None
        self.canvas: tk.Canvas | None = None
        self._view = CodeView()
        self._frame = 0
        self._snack = False
        self._generation = 0
        self._timer: str | None = None
        self._images: dict[tuple[int, int], tk.PhotoImage] = {}
        self._snacks: dict[int, tk.PhotoImage] = {}

    @property
    def windows(self) -> tuple[tk.Toplevel, ...]:
        return (self.window,) if self.window is not None else ()

    def show(self, view: CodeView) -> None:
        if all(slot is None for slot in view.slots):
            self._cancel()
            self._frame, self._snack = 0, False
        self._view = view
        if self.window is None:
            self.window = tk.Toplevel(self._root)
            self.window.withdraw()
            self.window.overrideredirect(True)
            background = '#ff00ff' if sys.platform == 'win32' else '#202733'
            self.window.configure(bg=background)
            if sys.platform == 'win32':
                self.window.wm_attributes('-toolwindow', True)
                self.window.wm_attributes('-transparentcolor', '#ff00ff')
            self.canvas = tk.Canvas(self.window, bg=background, bd=0,
                                    highlightthickness=0)
            self.canvas.pack()
        self.move()
        self.set_topmost(self._topmost())
        self._configure(self.window)
        self.window.deiconify()
        self._restore_stack()

    def _position(self) -> tuple[int, int, int]:
        anchor = self._anchor()
        scale = anchor.scale
        x = min(anchor.x + 150 * scale, anchor.right - 148 * scale)
        y = anchor.y + 194 * scale - 116 * scale
        return max(anchor.left, x), max(anchor.top, y), scale

    def point(self) -> tuple[float, float]:
        x, y, scale = self._position()
        return x + 55 * scale, y + 81 * scale

    def move(self) -> None:
        if self.window is None or self.canvas is None:
            return
        x, y, scale = self._position()
        self.window.geometry(f'{148 * scale}x{116 * scale}+{x}+{y}')
        self.canvas.configure(width=148 * scale, height=116 * scale)
        self._paint()

    def _paint(self) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        scale = self._anchor().scale
        key = self._frame, scale
        if key not in self._images:
            image = tk.PhotoImage(master=self._root, file=str(
                GAME_ART_DIR / 'mm-safe' / f'{self._frame:02d}.png',
            ))
            self._images[key] = image if scale == 2 else image.subsample(2)
        canvas.delete('all')
        canvas.create_image(0, 0, anchor='nw', image=self._images[key], tags='safe')
        if self._frame == 0:
            colors = {'red': '#db586c', 'yellow': '#f5c961', 'blue': '#73a6df',
                      'green': '#79b79a', 'purple': '#aa89ca', 'white': '#fff8ef'}
            for i, slot in enumerate(self._view.slots):
                x, y = (42 + 8 * i) * scale, 35 * scale
                canvas.create_oval(x - 2 * scale, y - 2 * scale,
                                   x + 2 * scale, y + 2 * scale,
                                   fill=colors.get(slot or '', '#9284a2'),
                                   outline='',
                                   tags='cover' if slot is None else 'piece')
        if self._snack and self._frame == 32:
            if scale not in self._snacks:
                source = tk.PhotoImage(master=self._root,
                                       file=str(GAME_ART_DIR / 'mm-donut.png'))
                width = 18 * scale
                divisor = math.gcd(source.width(), width)
                self._snacks[scale] = source.zoom(width // divisor).subsample(
                    source.width() // divisor,
                )
            canvas.create_image(55 * scale, 81 * scale,
                                image=self._snacks[scale], tags='snack')

    def _cancel(self) -> None:
        self._generation += 1
        if self._timer is not None:
            self._root.after_cancel(self._timer)
            self._timer = None

    def open(self, completed: Callable[[], None]) -> None:
        self._cancel()
        generation = self._generation

        def step(index: int) -> None:
            if generation != self._generation or self.window is None:
                return
            self._frame = index
            self._snack = index == 32
            self._paint()
            if index < 32:
                duration = round((index + 1) * 1560 / 32) - round(index * 1560 / 32)
                self._timer = self._root.after(duration, lambda: step(index + 1))
            else:
                self._timer = None
                completed()
        step(0)

    def snack(self, visible: bool) -> None:
        self._snack = visible
        self._paint()

    def set_topmost(self, enabled: bool) -> None:
        if self.window is not None:
            self.window.wm_attributes('-topmost', enabled)

    def hide(self) -> None:
        self._cancel()
        if self.window is not None:
            self.window.destroy()
        self.window = self.canvas = None
        self._view = CodeView()
        self._images.clear()
        self._snacks.clear()
