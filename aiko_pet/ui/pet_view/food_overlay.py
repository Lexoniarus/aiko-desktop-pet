"""Use native 1x/2x prepared food sprites at the authored hand anchors.

The image manifest is the sole source of pivot/size metadata. Feeding and
energy-drink effects stay exclusively in the existing pet care layer.
"""

from __future__ import annotations

import time
import tkinter as tk

from ...desktop.geometry import FOOT_BASELINE
from ...pet.animation.character import FRAME_WIDTH, AnimationClip, AnimationFrame
from ...pet.animation.item_assets import ItemCatalog


class FoodOverlay:
    """One Tk canvas item and reusable native-size sprite images."""

    def __init__(
        self, root: tk.Tk, canvas: tk.Canvas, *,
        catalog: ItemCatalog, scale: int,
    ) -> None:
        self._canvas = canvas
        self._foods = catalog.foods
        self._images = {
            (name, size): tk.PhotoImage(master=root, file=str(sprite.render_path))
            for name, food in self._foods.items()
            for size, sprite in food.sprites.items()
        }
        self.current_food_id: str | None = None
        self.item = canvas.create_image(0, 0, anchor="nw", state="hidden")
        self.foreground = canvas.create_image(0, 0, anchor="nw", state="hidden")
        self._hands: dict[tuple[str, int], tk.PhotoImage] = {}
        self.contact_origin: tuple[float, float] | None = None
        self._contact_at = 0.0
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
        self._contact_at = time.monotonic()
        if food_id is None:
            self._canvas.itemconfigure(self.item, state="hidden")
            self._canvas.itemconfigure(self.foreground, state="hidden")

    def render(
        self, clip: AnimationClip, frame: AnimationFrame, *,
        scale: int,
    ) -> None:
        item_id = self.current_food_id
        if (clip.name not in ("eat", "pick_up", "put_down")
                or frame.food_anchor is None or item_id is None):
            self._canvas.itemconfigure(self.item, state="hidden")
            self._canvas.itemconfigure(self.foreground, state="hidden")
            return
        sprite = self._foods[item_id].sprites[scale]
        image = self._images[(item_id, scale)]
        x: float = (FRAME_WIDTH // 2 - clip.anchor[0] + frame.food_anchor[0]) * scale
        y: float = (FOOT_BASELINE - clip.anchor[1] + frame.food_anchor[1]) * scale
        if self.contact_origin is not None and clip.name != "put_down":
            blend = min(1.0, (time.monotonic() - self._contact_at) / 0.13)
            x = self.contact_origin[0] * (1 - blend) + x * blend
            y = self.contact_origin[1] * (1 - blend) + y * blend
        self._canvas.coords(
            self.item, round(x - sprite.pivot[0]), round(y - sprite.pivot[1]),
        )
        self._canvas.itemconfigure(self.item, image=image, state="normal")
        self._canvas.tag_raise(self.item)
        self._canvas.itemconfigure(self.foreground, state="hidden")
        if frame.hand_foreground is not None:
            key = str(frame.hand_foreground), scale
            if key not in self._hands:
                hand = tk.PhotoImage(master=self._canvas,
                                     file=str(frame.hand_foreground))
                self._hands[key] = hand if scale == 1 else hand.zoom(scale)
            self._canvas.coords(self.foreground,
                                (FRAME_WIDTH // 2 - clip.anchor[0]) * scale,
                                (FOOT_BASELINE - clip.anchor[1]) * scale)
            self._canvas.itemconfigure(self.foreground, image=self._hands[key],
                                       state="normal")
            self._canvas.tag_raise(self.foreground)

    def close(self) -> None:
        self._canvas.delete(self.item)
        self._canvas.delete(self.foreground)
        self._hands.clear()
        self._images.clear()
