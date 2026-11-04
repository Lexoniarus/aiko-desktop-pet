"""Native form widgets authored in 4K coordinates using the shared UI transform.

No measurement pass, polling, per-window fitting or global Tk monkey patching.
Screen events/winfo geometry remain physical; canvas hit tests convert explicitly.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from .ui_scale import UiScale


class Layout:
    """Scale layout distances at submission, including later content updates."""

    ui_scale: UiScale

    def _layout(self, options: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
        return {
            k: self.ui_scale.distance(v) if k in keys and v != "" else v
            for k, v in options.items()
        }

    def _remember_layout(self, manager: str, options: dict[str, Any]) -> None:
        if not hasattr(self, "_placements"):
            self._placements: dict[str, dict[str, Any]] = {}
            self._columns: dict[Any, dict[str, Any]] = {}
            self._rows: dict[Any, dict[str, Any]] = {}
        self._placements.setdefault(manager, {}).update(options)

    def _rescale_layout(self) -> None:
        manager = getattr(self, "winfo_manager")()
        placements = getattr(self, "_placements", {})
        if manager in placements:
            keys = (("x", "y", "width", "height") if manager == "place"
                    else ("padx", "pady", "ipadx", "ipady"))
            getattr(super(), f"{manager}_configure")(
                **self._layout(placements[manager], keys),
            )
        for axis, entries in (("column", getattr(self, "_columns", {})),
                              ("row", getattr(self, "_rows", {}))):
            for index, options in entries.items():
                getattr(super(), f"grid_{axis}configure")(
                    index, self._layout(options, ("minsize", "pad")),
                )

    def pack_configure(self, cnf: Any = None, **kw: Any) -> None:
        self._remember_layout("pack", {**(cnf or {}), **kw})
        getattr(super(), "pack_configure")(**self._layout(
            {**(cnf or {}), **kw}, ("padx", "pady", "ipadx", "ipady"),
        ))

    pack = pack_configure

    def grid_configure(self, cnf: Any = None, **kw: Any) -> None:
        self._remember_layout("grid", {**(cnf or {}), **kw})
        getattr(super(), "grid_configure")(**self._layout(
            {**(cnf or {}), **kw}, ("padx", "pady", "ipadx", "ipady"),
        ))

    grid = grid_configure

    def place_configure(self, cnf: Any = None, **kw: Any) -> None:
        self._remember_layout("place", {**(cnf or {}), **kw})
        getattr(super(), "place_configure")(**self._layout(
            {**(cnf or {}), **kw}, ("x", "y", "width", "height"),
        ))

    place = place_configure

    def grid_columnconfigure(self, index: Any, cnf: Any = None, **kw: Any) -> Any:
        self._remember_layout("columns", {})
        self._columns.setdefault(index, {}).update({**(cnf or {}), **kw})
        return getattr(super(), "grid_columnconfigure")(
            index, self._layout({**(cnf or {}), **kw}, ("minsize", "pad")),
        )

    columnconfigure = grid_columnconfigure

    def grid_rowconfigure(self, index: Any, cnf: Any = None, **kw: Any) -> Any:
        self._remember_layout("rows", {})
        self._rows.setdefault(index, {}).update({**(cnf or {}), **kw})
        return getattr(super(), "grid_rowconfigure")(
            index, self._layout({**(cnf or {}), **kw}, ("minsize", "pad")),
        )

    rowconfigure = grid_rowconfigure


class Widget(Layout):
    pixel_options: tuple[str, ...] = ()

    def __init__(self, master: tk.Misc, **kwargs: Any) -> None:
        self.ui_scale = UiScale.for_widget(master)
        self._logical: dict[str, Any] = {}
        getattr(super(), "__init__")(master, **self._scaled(kwargs))

    def _scaled(self, options: dict[str, Any]) -> dict[str, Any]:
        result = {}
        for name, value in options.items():
            self._logical[name] = value
            if name == "font":
                value = self.ui_scale.font(value)
            elif name == "image":
                value = self.ui_scale.image_list(value)
            elif name in (*self.pixel_options, "padx", "pady", "borderwidth", "bd",
                          "highlightthickness", "wraplength"):
                value = self.ui_scale.distance(value)
            result[name] = value
        return result

    def configure(self, cnf: Any = None, **kwargs: Any) -> Any:
        if isinstance(cnf, str) or cnf is None and not kwargs:
            return getattr(super(), "configure")(cnf)
        return getattr(super(), "configure")(**self._scaled({**(cnf or {}), **kwargs}))

    config = configure

    def _rescale(self, ratio: float) -> None:
        options = dict(self._logical)
        # Text variables, commands and state remain on the same native widgets.
        getattr(super(), "configure")(**self._scaled(options))
        self._rescale_layout()

    def design(self, name: str) -> Any:
        """Authored option for drawing algorithms; cget stays native pixels."""
        return self._logical[name]


class Frame(Widget, tk.Frame):
    pixel_options = ("width", "height")


class Label(Widget, tk.Label):
    pass


class Button(Widget, tk.Button):
    pixel_options = ("width", "height")  # Illustrated native game cells.


class Checkbutton(Widget, tk.Checkbutton):
    pass


class Combobox(Widget, ttk.Combobox):
    pass


class Canvas(Widget, tk.Canvas):
    pixel_options = ("width", "height")

    def _draw_options(self, options: dict[str, Any]) -> dict[str, Any]:
        result = dict(options)
        for name in ("width", "activewidth", "disabledwidth", "height"):
            if name in result:
                result[name] = float(result[name]) * self.ui_scale.factor
        if "font" in result:
            result["font"] = self.ui_scale.font(result["font"])
        for name in ("image", "activeimage", "disabledimage"):
            if name in result:
                result[name] = self.ui_scale.image(result[name])
        return result

    def _create(self, itemType: str, args: Any, kw: Any) -> int:  # noqa: N803
        flat = getattr(tk, "_flatten")(args)
        options = dict(kw)
        if flat and isinstance(flat[-1], dict):
            options = {**flat[-1], **options}
            flat = flat[:-1]
        return int(getattr(super(), "_create")(
            itemType, tuple(float(v) * self.ui_scale.factor for v in flat),
            self._draw_options(options),
        ))

    def coords(self, *args: Any) -> Any:
        if len(args) == 1:
            return [self.ui_scale.logical(v) for v in getattr(super(), "coords")(*args)]
        values = getattr(tk, "_flatten")(args[1:])
        return getattr(super(), "coords")(
            args[0], *(float(v) * self.ui_scale.factor for v in values),
        )

    def itemconfigure(
        self, tagOrId: Any, cnf: Any = None, **kw: Any,  # noqa: N803
    ) -> Any:
        if isinstance(cnf, str) or cnf is None and not kw:
            return getattr(super(), "itemconfigure")(tagOrId, cnf, **kw)
        return getattr(super(), "itemconfigure")(
            tagOrId, self._draw_options({**(cnf or {}), **kw}),
        )

    itemconfig = itemconfigure

    def _rescale(self, ratio: float) -> None:
        super()._rescale(ratio)
        tk.Canvas.scale(self, "all", 0, 0, ratio, ratio)
        for item in self.find_all():
            kind = str(self.tk.call(str(self), "type", item))
            if kind in ("line", "rectangle", "polygon", "oval", "arc"):
                for name in ("width", "activewidth", "disabledwidth"):
                    value = float(self.tk.call(str(self), "itemcget", item, "-" + name))
                    self.tk.call(str(self), "itemconfigure", item, "-" + name,
                                 value * ratio)

    def logical(self, value: float) -> float:
        return self.ui_scale.logical(value)

    def screen_point(self, x: float, y: float) -> tuple[float, float]:
        factor = self.ui_scale.factor
        return self.winfo_rootx() + x * factor, self.winfo_rooty() + y * factor
