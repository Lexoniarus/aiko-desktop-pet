"""Small widget doubles for window-free owner/command tests, not visual QA."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator
from unittest.mock import patch


class Widget:
    def __init__(self, master: Any = None, **options: Any) -> None:
        self.master = master
        self.children: list[Widget] = []
        if isinstance(master, Widget):
            master.children.append(self)
        self.options = {"text": "", "state": "normal", **options}
        self.mapped = False
        self.destroyed = False
        self.bindings: dict[str, Any] = {}
        self._tags = (f"widget{id(self)}", "Widget", "all")

    def configure(self, cnf: Any = None, **options: Any) -> None:
        self.options.update(cnf or {})
        self.options.update(options)

    def cget(self, key: str) -> Any:
        return self.options.get(key, "")

    def pack(self, **kwargs: Any) -> None:
        self.mapped = True

    grid = place = pack

    def pack_forget(self) -> None:
        self.mapped = False

    place_forget = pack_forget

    def pack_propagate(self, _enabled: bool) -> None:
        pass

    def bind(self, sequence: str, callback: Any, add: str | None = None) -> str:
        self.bindings[sequence] = callback
        return sequence

    def bind_class(self, tag: str, sequence: str, callback: Any) -> None:
        self.bindings[tag + sequence] = callback

    def unbind_class(self, tag: str, sequence: str) -> None:
        self.bindings.pop(tag + sequence, None)

    def unbind(self, *args: Any) -> None:
        pass

    def bindtags(self, tags: Any = None) -> Any:
        if tags is not None:
            self._tags = tags
        return self._tags

    def winfo_children(self) -> list[Widget]:
        return self.children.copy()

    def winfo_width(self) -> int:
        return int(self.options.get("width", 660))

    def winfo_height(self) -> int:
        return int(self.options.get("height", 790))

    winfo_reqwidth = winfo_width
    winfo_reqheight = winfo_height

    def winfo_rootx(self) -> int:
        return 20

    winfo_rooty = winfo_rootx

    def winfo_screenheight(self) -> int:
        return 1080

    def winfo_screenwidth(self) -> int:
        return 1920

    def winfo_ismapped(self) -> bool:
        return self.mapped

    def update_idletasks(self) -> None:
        pass

    def wm_attributes(self, *args: Any) -> None:
        pass

    overrideredirect = protocol = title = geometry = wm_attributes

    def withdraw(self) -> None:
        self.mapped = False

    def deiconify(self) -> None:
        self.mapped = True

    def lift(self) -> None:
        pass

    focus_set = lift

    def invoke(self) -> Any:
        if self.cget("state") != "disabled":
            if "variable" in self.options:
                variable = self.options["variable"]
                variable.set(not variable.get())
            return self.options["command"]()
        return None

    def set_selected(self, selected: bool) -> None:
        self.options["selected"] = selected

    def create_window(self, *args: Any, **kwargs: Any) -> int:
        return 1

    create_image = create_polygon = create_rectangle = create_window

    def coords(self, *args: Any, **kwargs: Any) -> None:
        pass

    itemconfigure = coords

    def set(self, *args: Any) -> None:
        pass

    def bbox(self, *_args: Any) -> tuple[int, int, int, int]:
        return 0, 0, 660, 790

    def xview(self, *args: Any) -> None:
        pass

    yview = xview_scroll = yview_scroll = yview_moveto = xview_moveto = xview

    def destroy(self) -> None:
        self.destroyed = True
        for child in self.children.copy():
            child.destroy()
        if isinstance(self.master, Widget):
            self.master.children.remove(self)


class Boolean:
    def __init__(self, **kwargs: Any) -> None:
        self._value = False

    def get(self) -> bool:
        return self._value

    def set(self, value: bool) -> None:
        self._value = value


class Images:
    def icon(self, *_args: Any) -> object:
        return object()

    surface = file = icon


class Skin:
    background = "#FCF7F9"
    panel = "#EDF4FA"
    border = "#B8CDDF"
    title = "#FFFFFF"
    text = "#3E4C61"
    muted = accent = "#65758A"
    font = "Segoe UI"
    small_line_height = 11

    def __init__(self, *_args: Any) -> None:
        self.images = Images()

    def frame(self, parent: Any) -> Widget:
        return Widget(parent)

    def header(self, parent: Any, text: str) -> Widget:
        return Widget(parent, text=text)

    def button(self, parent: Any, text: str, command: Any, **kwargs: Any) -> Widget:
        return Widget(parent, text=text, command=command)


@contextmanager
def widgets() -> Iterator[None]:
    with (
        patch.multiple(
            "tkinter",
            Frame=Widget,
            Label=Widget,
            Canvas=Widget,
            Scrollbar=Widget,
            Toplevel=Widget,
            Button=Widget,
            Checkbutton=Widget,
            BooleanVar=Boolean,
        ),
        patch("tkinter.Tk", side_effect=AssertionError("Native windows prohibited")),
    ):
        yield
