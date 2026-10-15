"""Small passive windows for World items; no second mutable object store."""

from __future__ import annotations

import sys
import tkinter as tk

from ..desktop.object_windows import make_object_window_passive
from ..pet.animation.item_assets import ItemCatalog
from ..world.contracts import ObjectState, WorldSnapshot
from .pet_view.desktop_window import MAGENTA


class WorldView:
    def __init__(self, root: tk.Tk, items: ItemCatalog) -> None:
        self.root = root
        self.items = items
        self._images: dict[tuple[str, int], tk.PhotoImage] = {}
        self._windows: dict[str, tuple[tk.Toplevel, tk.Label]] = {}

    @property
    def windows(self) -> list[tk.Toplevel]:
        return [entry[0] for entry in self._windows.values()]

    def image(self, asset_id: str, scale: int) -> tk.PhotoImage:
        key = asset_id, scale
        if key not in self._images:
            self._images[key] = tk.PhotoImage(
                master=self.root,
                file=str(self.items.foods[asset_id].sprites[scale].render_path),
            )
        return self._images[key]

    def sync(
        self, snapshot: WorldSnapshot, *, left: float, ground_y: float,
        scale: int, topmost: bool,
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
                self._windows[item.instance_id] = window, label
            else:
                window, label = entry
            label.configure(image=image)
            window.wm_attributes("-topmost", topmost)
            x = round(left + item.position.x - image.width() / 2)
            y = round(ground_y - item.position.height - image.height())
            if item.state == ObjectState.USER_HELD and carried_cursor is not None:
                grip = self.items.foods[asset_id].sprites[scale].pivot
                x = round(carried_cursor[0] - grip[0])
                y = round(carried_cursor[1] - grip[1])
            window.geometry(f"{image.width()}x{image.height()}{x:+d}{y:+d}")
            if entry is None:
                window.update_idletasks()
                make_object_window_passive(window)
            window.deiconify()
            if item.state == ObjectState.USER_HELD:
                make_object_window_passive(window, x=x, y=y)
        for token in tuple(self._windows):
            if token not in visible:
                self._windows.pop(token)[0].destroy()

    def close(self) -> None:
        for window, _label in self._windows.values():
            window.destroy()
        self._windows.clear()
        self._images.clear()
