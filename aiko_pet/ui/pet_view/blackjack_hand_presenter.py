"""Aiko's persistent floating hand, independent of speech and World objects."""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable

from ..common.playing_card_images import PlayingCardImages
from ..view_models.game_models import HandAnchor, HandView, place_hand


class BlackjackHandPresenter:
    def __init__(
        self, root: tk.Tk, *, images: PlayingCardImages,
        anchor: Callable[[], HandAnchor], topmost: Callable[[], bool],
        configure_window: Callable[[tk.Toplevel], None],
        restore_stack: Callable[[], object],
    ) -> None:
        self._root, self._images, self._anchor = root, images, anchor
        self._topmost, self._configure = topmost, configure_window
        self._restore_stack = restore_stack
        self.window: tk.Toplevel | None = None
        self.canvas: tk.Canvas | None = None
        self._hand = HandView()
        self._previous = HandView()
        self._hover = -1
        self._flip_index = -1
        self._frame = 0
        self.pending_timer: str | None = None

    @property
    def windows(self) -> tuple[tk.Toplevel, ...]:
        return (self.window,) if self.window is not None else ()

    def show(self, hand: HandView, flip: bool = False) -> None:
        if not hand.cards:
            self.hide()
            return
        self._cancel_timer()
        self._previous, self._hand = self._hand, hand
        self._hover = -1
        self._frame = 0
        self._flip_index = next((
            i for i, (old, new) in enumerate(zip(self._previous.cards, hand.cards))
            if old is None and new is not None
        ), -1) if flip else -1
        if self.window is None:
            self.window = tk.Toplevel(self._root)
            self.window.withdraw()
            self.window.overrideredirect(True)
            self.window.configure(bg="#ff00ff")
            self.window.wm_attributes("-topmost", self._topmost())
            if sys.platform == "win32":
                self.window.wm_attributes("-toolwindow", True)
                self.window.wm_attributes("-transparentcolor", "#ff00ff")
            self.canvas = tk.Canvas(
                self.window, bg="#ff00ff", bd=0, highlightthickness=0,
            )
            self.canvas.pack()
            self.canvas.bind("<Motion>", self._motion)
            self.canvas.bind("<Leave>", self._leave)
            self.canvas.bind("<ButtonPress-1>", lambda _event: "break")
            self.canvas.bind("<ButtonPress-3>", lambda _event: "break")
        self.move()
        self._configure(self.window)
        self.window.wm_attributes("-topmost", self._topmost())
        self.window.deiconify()
        self._restore_stack()
        if self._flip_index >= 0:
            self.pending_timer = self._root.after(45, self.advance_flip)

    def move(self) -> None:
        if self.window is None or self.canvas is None:
            return
        anchor = self._anchor()
        layout = place_hand(len(self._hand.cards), anchor)
        self.window.geometry(
            f"{layout.width}x{layout.height}+{layout.x}+{layout.y}",
        )
        self.canvas.configure(width=layout.width, height=layout.height)
        self._render()

    def _render(self) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        canvas.delete("all")
        anchor = self._anchor()
        layout = place_hand(len(self._hand.cards), anchor)
        for i, face in enumerate(self._hand.cards):
            compression = 1
            if i == self._flip_index:
                compression = (1, 2, 4, 8, 8, 4, 2, 1)[self._frame]
                if self._frame < 4:
                    face = None
            image = self._images.get(face, anchor.scale, compression)
            x = i * layout.step + 32 * anchor.scale
            y = (4 if i == self._hover else 8) * anchor.scale
            canvas.create_image(x, y, anchor="n", image=image, tags=(f"card_{i}",))

    def advance_flip(self) -> None:
        self._cancel_timer()
        if self.window is None or self._flip_index < 0:
            return
        self._frame += 1
        if self._frame >= 8:
            self._flip_index = -1
        self._render()
        if self._flip_index >= 0:
            self.pending_timer = self._root.after(45, self.advance_flip)

    def _motion(self, event: tk.Event) -> None:
        if self._flip_index >= 0:
            return
        anchor = self._anchor()
        layout = place_hand(len(self._hand.cards), anchor)
        hit = -1
        for i in reversed(range(len(self._hand.cards))):
            x = event.x - i * layout.step
            y = event.y - (4 if i == self._hover else 8) * anchor.scale
            image = self._images.get(self._hand.cards[i], anchor.scale)
            if (0 <= x < image.width() and 0 <= y < image.height()
                    and not image.transparency_get(x, y)):
                hit = i
                break
        if self._hover != hit:
            self._hover = hit
            self._render()

    def _leave(self, _event: tk.Event) -> None:
        self._hover = -1
        self._render()

    def set_topmost(self, enabled: bool) -> None:
        if self.window is not None:
            self.window.wm_attributes("-topmost", enabled)

    def _cancel_timer(self) -> None:
        if self.pending_timer is not None:
            self._root.after_cancel(self.pending_timer)
            self.pending_timer = None

    def hide(self) -> None:
        self._cancel_timer()
        if self.window is not None:
            self.window.destroy()
        self.window = None
        self.canvas = None
        self._hand = HandView()
        self._previous = HandView()
        self._flip_index = -1
