"""Project item windows and offer pixel-local pickup for resting portions."""

from __future__ import annotations

import sys
import time
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass, replace
from functools import partial

from ..desktop.object_windows import configure_object_window
from ..pet.animation.item_assets import ItemCatalog, ItemSprite
from ..world.contracts import ObjectState, WorldSnapshot
from .pet_view.desktop_window import MAGENTA


@dataclass
class _ObjectWindow:
    window: tk.Toplevel
    label: tk.Label
    interactive: bool | None = None
    revision: int = -1
    image: tk.PhotoImage | None = None


class WorldView:
    def __init__(
        self,
        root: tk.Tk,
        items: ItemCatalog,
        *,
        pickup: Callable[[str, int], None] = lambda _token, _revision: None,
    ) -> None:
        self.root = root
        self.items = items
        self._images: dict[tuple[str, int], tk.PhotoImage] = {}
        self._windows: dict[str, _ObjectWindow] = {}
        self._pickup = pickup

    @property
    def windows(self) -> list[tk.Toplevel]:
        return [entry.window for entry in self._windows.values()]

    def _press(self, token: str, event: tk.Event[tk.Label]) -> str:
        entry = self._windows.get(token)
        image = entry.image if entry is not None else None
        if (entry is not None and entry.interactive and image is not None
                and 0 <= event.x < image.width() and 0 <= event.y < image.height()
                and not image.transparency_get(event.x, event.y)
                and image.get(event.x, event.y) != (255, 0, 255)):
            self._pickup(token, entry.revision)
        # Item input must never bubble into the pet's care or drag bindings.
        return "break"

    def sprite(self, asset_id: str, scale: int) -> ItemSprite:
        book = self.items.readables.get(asset_id)
        if book is None:
            return self.items.foods[asset_id].sprites[scale]
        # Prefer the native larger source before integer magnification.
        target_scale = scale * book.world_zoom
        source_scale = min(target_scale, 2)
        sprite = book.sprites[source_scale]
        zoom = target_scale // source_scale
        return replace(sprite, pivot=(sprite.pivot[0] * zoom,
                                      sprite.pivot[1] * zoom), zoom=zoom)

    def image(self, asset_id: str, scale: int) -> tk.PhotoImage:
        key = asset_id, scale
        if key not in self._images:
            sprite = self.sprite(asset_id, scale)
            image = tk.PhotoImage(master=self.root, file=str(sprite.render_path))
            self._images[key] = image.zoom(sprite.zoom) if sprite.zoom != 1 else image
        return self._images[key]

    def ground_pivot(self, asset_id: str, scale: int) -> tuple[float, float]:
        if asset_id in self.items.readables:
            return self.sprite(asset_id, scale).pivot
        image = self.image(asset_id, scale)
        return image.width() / 2, image.height()

    def sync(
        self,
        snapshot: WorldSnapshot,
        *,
        left: float,
        ground_y: float,
        scale: int,
        topmost: bool,
        carried_cursor: tuple[int, int] | None = None,
    ) -> None:
        definitions = {item.definition_id: item for item in snapshot.definitions}
        visible: set[str] = set()
        for item in snapshot.objects:
            if item.position is None:
                continue
            visible.add(item.instance_id)
            asset_id = definitions[item.definition_id].asset_id
            image = self.image(asset_id, scale)
            entry = self._windows.get(item.instance_id)
            if entry is None:
                window = tk.Toplevel(self.root)
                window.withdraw()
                window.overrideredirect(True)
                window.configure(bg=MAGENTA)
                if sys.platform == "win32":
                    window.wm_attributes("-transparentcolor", MAGENTA)
                    window.wm_attributes("-toolwindow", True)
                label = tk.Label(window, bg=MAGENTA, bd=0, highlightthickness=0)
                label.pack()
                entry = _ObjectWindow(window, label)
                self._windows[item.instance_id] = entry
                label.bind("<ButtonPress-1>", partial(self._press, item.instance_id))
            else:
                window, label = entry.window, entry.label
            label.configure(image=image)
            entry.image = image
            window.wm_attributes("-topmost", topmost)
            if item.expires_at is not None:
                window.wm_attributes(
                    "-alpha", max(0.0, min(1.0, item.expires_at - time.time()))
                )
            support = self.ground_pivot(asset_id, scale)
            x = round(left + item.position.x - support[0])
            y = round(ground_y - item.position.height - support[1])
            if item.state == ObjectState.USER_HELD and carried_cursor is not None:
                grip = self.sprite(asset_id, scale).pivot
                x = round(carried_cursor[0] - grip[0])
                y = round(carried_cursor[1] - grip[1])
            window.geometry(f"{image.width()}x{image.height()}{x:+d}{y:+d}")
            interactive = item.state == ObjectState.RESTING
            if entry.interactive != interactive:
                window.update_idletasks()
                configure_object_window(window, interactive=interactive)
                entry.interactive = interactive
            entry.revision = item.revision
            window.deiconify()
            if item.state == ObjectState.USER_HELD:
                configure_object_window(window, x=x, y=y)
        for token in tuple(self._windows):
            if token not in visible:
                self._windows.pop(token).window.destroy()

    def close(self) -> None:
        for entry in self._windows.values():
            entry.window.destroy()
        self._windows.clear()
        self._images.clear()
