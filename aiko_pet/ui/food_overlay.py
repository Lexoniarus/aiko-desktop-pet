"""Small food assets follow the eat clip's per-frame hand anchors."""

from __future__ import annotations

import tkinter as tk

from ..presentation.character import AnimationClip, AnimationFrame
from ..presentation.food_models import FoodChoice, food_choices
from ..presentation.character import FRAME_WIDTH
from ..desktop.geometry import FOOT_BASELINE


class FoodOverlay:
    """Own cached Tk images and one sprite-relative overlay canvas item."""

    SOURCE_SUBSAMPLE = 3
    # Source food PNGs were prepared at 98% of the original hand-object size.

    def __init__(
        self, root: tk.Tk, canvas: tk.Canvas, *,
        scale: int,
        choices: tuple[FoodChoice, ...] | None = None,
    ) -> None:
        self._root = root
        self._canvas = canvas
        self._choices = choices if choices is not None else food_choices()
        self._images: dict[str, tk.PhotoImage] = {}
        self.current_food_id: str | None = None
        self.item = canvas.create_image(
            0, 0, anchor="s", state="hidden",
        )
        self.reload(scale)

    def reload(self, scale: int) -> None:
        self._images.clear()
        for food in self._choices:
            if not food.image_path.is_file():
                continue
            source = tk.PhotoImage(master=self._root, file=str(food.image_path))
            image = source.subsample(self.SOURCE_SUBSAMPLE)
            self._images[food.id] = image if scale == 1 else image.zoom(scale)
        self._canvas.itemconfigure(self.item, state="hidden")

    def select(self, food_id: str | None) -> None:
        """Set only the visual selection; consumption is a domain operation."""
        self.current_food_id = food_id
        if food_id is None:
            self._canvas.itemconfigure(self.item, state="hidden")

    def render(
        self, clip: AnimationClip, frame: AnimationFrame, *,
        scale: int,
    ) -> None:
        image = self._images.get(self.current_food_id or "")
        if clip.name != "eat" or frame.food_anchor is None or image is None:
            self._canvas.itemconfigure(self.item, state="hidden")
            return
        x = (FRAME_WIDTH // 2 - clip.anchor[0] + frame.food_anchor[0]) * scale
        y = (FOOT_BASELINE - clip.anchor[1] + frame.food_anchor[1]) * scale
        self._canvas.coords(self.item, x, y)
        self._canvas.itemconfigure(self.item, image=image, state="normal")
        self._canvas.tag_raise(self.item)

    def close(self) -> None:
        self._canvas.delete(self.item)
        self._images.clear()
