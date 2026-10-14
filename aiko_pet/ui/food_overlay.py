"""Use native 1x/2x prepared food sprites at the authored hand anchors.

The image manifest is the sole source of pivot/size metadata. Feeding and
energy-drink effects stay exclusively in the existing pet care layer.
"""

from __future__ import annotations

import tkinter as tk

from ..desktop.geometry import FOOT_BASELINE
from ..infrastructure.item_assets import load_item_catalog
from ..pet.animation.character import AnimationClip, AnimationFrame, FRAME_WIDTH


class FoodOverlay:
    """One Tk canvas item and reusable native-size sprite images."""

    def __init__(
        self, root: tk.Tk, canvas: tk.Canvas, *, scale: int,
    ) -> None:
        self._canvas = canvas
        self._foods = load_item_catalog().foods
        self._images = {
            (name, size): tk.PhotoImage(master=root, file=str(sprite.path))
            for name, food in self._foods.items()
            for size, sprite in food.sprites.items()
        }
        self.current_food_id: str | None = None
        self.item = canvas.create_image(0, 0, anchor="nw", state="hidden")
        self.reload(scale)

    def reload(self, scale: int) -> None:
        """Switch scale without resampling or reloading image files."""
        if scale not in (1, 2):
            raise ValueError("Food overlay scale must be 1 or 2")
        self._scale = scale
        self._canvas.itemconfigure(self.item, state="hidden")

    def select(self, food_id: str | None) -> None:
        """Select a validated visual asset, never award any need."""
        if food_id is not None and food_id not in self._foods:
            raise ValueError(f"Unknown food overlay: {food_id}")
        self.current_food_id = food_id
        if food_id is None:
            self._canvas.itemconfigure(self.item, state="hidden")

    def render(
        self, clip: AnimationClip, frame: AnimationFrame, *,
        scale: int,
    ) -> None:
        item_id = self.current_food_id
        if clip.name != "eat" or frame.food_anchor is None or item_id is None:
            self._canvas.itemconfigure(self.item, state="hidden")
            return
        sprite = self._foods[item_id].sprites[scale]
        image = self._images[(item_id, scale)]
        x = (FRAME_WIDTH // 2 - clip.anchor[0] + frame.food_anchor[0]) * scale
        y = (FOOT_BASELINE - clip.anchor[1] + frame.food_anchor[1]) * scale
        self._canvas.coords(
            self.item, round(x - sprite.pivot[0]), round(y - sprite.pivot[1]),
        )
        self._canvas.itemconfigure(self.item, image=image, state="normal")
        self._canvas.tag_raise(self.item)

    def close(self) -> None:
        self._canvas.delete(self.item)
        self._images.clear()
