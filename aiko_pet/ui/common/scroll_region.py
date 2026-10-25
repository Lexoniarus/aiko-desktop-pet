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
        autohide: bool = False,
        fit_content: bool = False,
        max_height: int | None = None,
        background: str | None = None,
    ) -> None:
        color = background or skin.background
        self.frame = tk.Frame(parent, bg=color)
        self.canvas = tk.Canvas(
            self.frame,
            width=width,
            height=height,
            bg=color,
            bd=0,
            highlightthickness=0,
            takefocus=True,
        )
        self.body = tk.Frame(self.canvas, bg=color)
        self._horizontal = horizontal
        self._autohide = autohide
        self._fit_content = fit_content
        self._max_height = max_height
        self._bar_visible = not autohide
        self._layout_idle: str | None = None
        self._pointer_focus: tk.Misc | None = None
        self._item = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        # Autohiding must not change the viewport width and reflow its content.
        # A fixed gutter also breaks the parent-size/overflow feedback cycle.
        self._gutter: tk.Frame | None = None
        if autohide and not horizontal:
            self._gutter = tk.Frame(self.frame, width=10, height=1, bg=color)
            self._gutter.pack(side="right", fill="y")
            self._gutter.pack_propagate(False)
        self.scrollbar = tk.Scrollbar(
            self._gutter if self._gutter is not None else self.frame,
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
            if not autohide:
                self.scrollbar.pack(side="bottom", fill="x")
            self.canvas.configure(xscrollcommand=self.scrollbar.set)
        else:
            if not autohide:
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
            self.canvas.bind_class(
                self._tag, f"<{key}>", partial(self._key_scroll, amount)
            )
        self.canvas.bind_class(self._tag, "<FocusIn>", self._focus_visible)
        self.canvas.bind_class(self._tag, "<ButtonPress-1>", self._pointer_pressed)
        self.canvas.bind_class(self._tag, "<ButtonRelease-1>", self._pointer_released)
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
                widget.bindtags((self._tag, *tags))
            for child in widget.winfo_children():
                visit(child)

        visit(self.canvas)

    def _key_scroll(self, amount: int, _event: tk.Event) -> str:
        return self._scroll(amount)

    def _focus_visible(self, event: tk.Event) -> None:
        """Tabbing to an offscreen card/choice reveals it without stealing focus."""
        widget = event.widget
        pointer_focus, self._pointer_focus = self._pointer_focus, None
        if widget is pointer_focus:
            # Native buttons focus on press. Scrolling them at that instant can
            # move them out from under the pointer and cancel the first click.
            return
        if widget is self.canvas:
            return
        if self._horizontal:
            low = widget.winfo_rootx() - self.canvas.winfo_rootx()
            high = low + widget.winfo_width()
            extent, total = self.canvas.winfo_width(), self.body.winfo_reqwidth()
            offset = low if low < 0 else max(0, high - extent)
            if offset and total > 0:
                self.canvas.xview_moveto(
                    max(0, self.canvas.xview()[0] + offset / total)
                )
        else:
            low = widget.winfo_rooty() - self.canvas.winfo_rooty()
            high = low + widget.winfo_height()
            extent, total = self.canvas.winfo_height(), self.body.winfo_reqheight()
            offset = low if low < 0 else max(0, high - extent)
            if offset and total > 0:
                self.canvas.yview_moveto(
                    max(0, self.canvas.yview()[0] + offset / total)
                )

    def _pointer_pressed(self, event: tk.Event) -> None:
        self._pointer_focus = event.widget

    def _pointer_released(self, _event: tk.Event) -> None:
        self._pointer_focus = None

    def _scroll(self, amount: int) -> str:
        if self._horizontal:
            self.canvas.xview_scroll(amount, "units")
        else:
            self.canvas.yview_scroll(amount, "units")
        return "break"

    def _wheel(self, event: tk.Event) -> str:
        return self._scroll(-1 if event.delta > 0 else 1)

    def refresh_layout(self) -> None:
        """Settle changed children even if Tk unmapped an offscreen canvas item."""
        if self._layout_idle is None:
            self._layout_idle = self.frame.after_idle(self._settle_content)

    def _settle_content(self) -> None:
        self._layout_idle = None
        if self._horizontal:
            self.canvas.itemconfigure(self._item, width=0)
        self._content_changed(None)

    def _content_changed(self, _event: tk.Event | None) -> None:
        self.canvas.configure(scrollregion=(
            0, 0, self.body.winfo_reqwidth(), self.body.winfo_reqheight(),
        ))
        if self._fit_content:
            height = self.body.winfo_reqheight()
            if self._max_height is not None:
                height = min(height, self._max_height)
            if int(self.canvas.cget("height")) != max(1, height):
                self.canvas.configure(height=max(1, height))
        self._sync_scrollbar()
        self.adopt()

    def _viewport_changed(self, event: tk.Event) -> None:
        if not self._horizontal:
            self.canvas.itemconfigure(self._item, width=event.width)
        self._sync_scrollbar()

    def _sync_scrollbar(self) -> None:
        if not self._autohide:
            return
        extent = (
            self.canvas.winfo_width() if self._horizontal
            else self.canvas.winfo_height()
        )
        total = (
            self.body.winfo_reqwidth() if self._horizontal
            else self.body.winfo_reqheight()
        )
        visible = total > extent + 1
        if visible == self._bar_visible:
            return
        self._bar_visible = visible
        if visible:
            if self._gutter is not None:
                self.scrollbar.pack(fill="both", expand=True)
            else:
                self.scrollbar.pack(
                    side="bottom" if self._horizontal else "right",
                    fill="x" if self._horizontal else "y", before=self.canvas,
                )
        else:
            self.scrollbar.pack_forget()
            if self._horizontal:
                self.canvas.xview_moveto(0)
            else:
                self.canvas.yview_moveto(0)

    def _destroyed(self, event: tk.Event) -> None:
        if event.widget is self.frame:
            if self._layout_idle is not None:
                self.frame.after_cancel(self._layout_idle)
                self._layout_idle = None
            for sequence in (
                "<MouseWheel>",
                "<Button-4>",
                "<Button-5>",
                "<FocusIn>",
                "<ButtonPress-1>",
                "<ButtonRelease-1>",
                "<Up>",
                "<Down>",
                "<Prior>",
                "<Next>",
                "<Left>",
                "<Right>",
            ):
                self.canvas.unbind_class(self._tag, sequence)
