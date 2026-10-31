"""Aiko's persistent floating hand, independent of speech and World objects."""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable

from ...games.blackjack import hand_total
from ..common.game_pacing import GAME_PACING
from ..common.playing_card_images import PlayingCardImages
from ..view_models.game_models import HandAnchor, HandLayout, HandView, place_hand


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
        self._background = "#ff00ff" if sys.platform == "win32" else "#202733"
        self.window: tk.Toplevel | None = None
        self.canvas: tk.Canvas | None = None
        self.caption: tk.Label | None = None
        # Unmapped measurement keeps targets accurate before the first card lands.
        self._caption_measure = self._make_caption(root)
        self._caption_measure.configure(text="BANK · AIKO · verdeckt")
        self._caption_width = 0
        self._hand = HandView()
        self._previous = HandView()
        self._hover = -1
        self._flip_index = -1
        self._frame = 0
        self.pending_timer: str | None = None
        self._generation = 0

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
            self.window.configure(bg=self._background)
            self.window.wm_attributes("-topmost", self._topmost())
            if sys.platform == "win32":
                self.window.wm_attributes("-toolwindow", True)
                self.window.wm_attributes("-transparentcolor", "#ff00ff")
            self.canvas = tk.Canvas(
                self.window, bg=self._background, bd=0, highlightthickness=0,
            )
            self.canvas.pack()
            self.caption = self._make_caption(self.window)
            self.caption.pack(fill="x")
            self.caption.bind("<ButtonPress-1>", lambda _event: "break")
            self.caption.bind("<ButtonPress-3>", lambda _event: "break")
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
            self._queue_flip()

    def move(self) -> None:
        if self.window is None or self.canvas is None:
            return
        layout = self._layout(len(self._hand.cards))
        self.window.geometry(
            f"{layout.width}x{layout.height}+{layout.x}+{layout.y}",
        )
        self.canvas.configure(width=layout.width, height=144)
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
            image = self._images.get(face, 2, compression)
            x = i * layout.step + 64
            y = (8 if i == self._hover else 16)
            canvas.create_image(x, y, anchor="n", image=image, tags=(f"card_{i}",))

        public = tuple(card for card in self._hand.cards if card is not None)
        caption = "BANK · AIKO"
        if self._flip_index < 0:
            caption += (" · verdeckt" if len(public) != len(self._hand.cards)
                        else f" · {hand_total(public)}")
        if self.caption is not None:
            self.caption.configure(text=caption, wraplength=max(1, layout.width - 14))

    @staticmethod
    def _make_caption(parent: tk.Misc) -> tk.Label:
        return tk.Label(parent, font=("Segoe UI", 9, "bold"), padx=6, pady=4,
                        bd=0, highlightthickness=1, highlightbackground="#B8CDDF",
                        highlightcolor="#B8CDDF",
                        bg="#FCF7F9", fg="#624668")

    def _layout(self, count: int) -> HandLayout:
        anchor = self._anchor()
        width = place_hand(count, anchor).width
        if width != self._caption_width:
            self._caption_measure.configure(wraplength=max(1, width - 14))
            self._caption_width = width
        return place_hand(count, anchor,
                          caption_height=self._caption_measure.winfo_reqheight())

    def _queue_flip(self) -> None:
        generation = self._generation
        self.pending_timer = self._root.after(
            GAME_PACING.card_flip_frame_ms,
            lambda: self._flip_if_current(generation),
        )

    def _flip_if_current(self, generation: int) -> None:
        if generation == self._generation:
            self.advance_flip()

    def advance_flip(self) -> None:
        self._cancel_timer()
        if self.window is None or self._flip_index < 0:
            return
        self._frame += 1
        if self._frame >= 8:
            self._flip_index = -1
        self._render()
        if self._flip_index >= 0:
            self._queue_flip()

    def _motion(self, event: tk.Event) -> None:
        if self._flip_index >= 0:
            return
        anchor = self._anchor()
        layout = place_hand(len(self._hand.cards), anchor)
        hit = -1
        for i in reversed(range(len(self._hand.cards))):
            x = event.x - i * layout.step
            y = event.y - (8 if i == self._hover else 16)
            image = self._images.get(self._hand.cards[i], 2)
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

    def point(self, index: int, count: int) -> tuple[float, float]:
        layout = self._layout(count)
        return layout.x + index * layout.step, layout.y + 16

    def set_topmost(self, enabled: bool) -> None:
        if self.window is not None:
            self.window.wm_attributes("-topmost", enabled)

    def _cancel_timer(self) -> None:
        self._generation += 1
        if self.pending_timer is not None:
            self._root.after_cancel(self.pending_timer)
            self.pending_timer = None

    def hide(self) -> None:
        self._cancel_timer()
        if self.window is not None:
            self.window.destroy()
        self.window = None
        self.canvas = None
        self.caption = None
        self._hand = HandView()
        self._previous = HandView()
        self._flip_index = -1
