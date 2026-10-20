"""Local scrolling, including keyboard/wheel input, without global input hooks."""

from __future__ import annotations

import tkinter as tk
from functools import partial

from .skin import AikoSkin


class ScrollRegion:
    def __init__(
        self,
        parent: tk.Misc,
        skin: AikoSkin,
        *,
        width: int = 300,
        height: int = 220,
        horizontal: bool = False,
    ) -> None:
        self.frame = tk.Frame(parent, bg=skin.background)
        self.canvas = tk.Canvas(
            self.frame,
            width=width,
            height=height,
            bg=skin.background,
            bd=0,
            highlightthickness=0,
            takefocus=True,
        )
        self.body = tk.Frame(self.canvas, bg=skin.background)
        self._horizontal = horizontal
        self._item = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.scrollbar = tk.Scrollbar(
            self.frame,
            orient="horizontal" if horizontal else "vertical",
            command=self.canvas.xview if horizontal else self.canvas.yview,
            width=10,
            bg="#FCF7F9",
            troughcolor="#F8F1F5",
            activebackground="#94ABC2",
            bd=0,
            highlightthickness=0,
        )
        if horizontal:
            self.scrollbar.pack(side="bottom", fill="x")
            self.canvas.configure(xscrollcommand=self.scrollbar.set)
        else:
            self.scrollbar.pack(side="right", fill="y")
            self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self._tag = f"VnScroll{self.canvas}"
        self.canvas.bind_class(self._tag, "<MouseWheel>", self._wheel)
        self.canvas.bind_class(self._tag, "<Button-4>", lambda _e: self._scroll(-1))
        self.canvas.bind_class(self._tag, "<Button-5>", lambda _e: self._scroll(1))
        for key, amount in (
            ("Up", -1),
            ("Down", 1),
            ("Prior", -5),
            ("Next", 5),
            ("Left", -1),
            ("Right", 1),
        ):
            self.canvas.bind(f"<{key}>", partial(self._key_scroll, amount))
        self.body.bind("<Configure>", self._content_changed)
        self.canvas.bind("<Configure>", self._viewport_changed)
        self.frame.bind("<Destroy>", self._destroyed, add="+")
        self.adopt()

    def adopt(self) -> None:
        """Attach this local scroll tag before outer regions; never bind_all."""

        def visit(widget: tk.Misc) -> None:
            tags = list(widget.bindtags())
            if any(t.startswith("VnScroll") and t != self._tag for t in tags):
                return
            if self._tag not in tags:
                widget.bindtags((tags[0], self._tag, *tags[1:]))
            for child in widget.winfo_children():
                visit(child)

        visit(self.canvas)

    def _key_scroll(self, amount: int, _event: tk.Event) -> str:
        return self._scroll(amount)

    def _scroll(self, amount: int) -> str:
        if self._horizontal:
            self.canvas.xview_scroll(amount, "units")
        else:
            self.canvas.yview_scroll(amount, "units")
        return "break"

    def _wheel(self, event: tk.Event) -> str:
        return self._scroll(-1 if event.delta > 0 else 1)

    def _content_changed(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.adopt()

    def _viewport_changed(self, event: tk.Event) -> None:
        if not self._horizontal:
            self.canvas.itemconfigure(self._item, width=event.width)

    def _destroyed(self, event: tk.Event) -> None:
        if event.widget is self.frame:
            for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                self.canvas.unbind_class(self._tag, sequence)
