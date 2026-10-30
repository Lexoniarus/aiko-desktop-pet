"""Tk speech and emote display, independent of application/domain decisions."""

from __future__ import annotations

import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ...asset_paths import EMOTE_IMAGE_DIR
from ...games.rock_paper_scissors import Move
from ...pet.content import GERMAN_TEXT
from ...pet.mind.reaction_sequence import EMOTES
from ..common.icon_images import IconImages
from ..common.rounded_panel import RoundedPanel


@dataclass(frozen=True, slots=True)
class SpeechAnchor:
    """Desktop-screen anchor of the sprite, not of any toolbar widget."""

    x: int
    y: int
    width: int


class SpeechPresenter:
    """Own the active Tk speech window, emote image cache and hide timer.

    The desktop shell injects geometry and z-order callbacks; no pet or
    notification/transport objects are imported by this presenter.
    """

    def __init__(
        self,
        *,
        root: tk.Tk,
        anchor: Callable[[], SpeechAnchor],
        font_name: str,
        always_on_top: Callable[[], bool],
        restore_stack: Callable[[], object],
        transparent_color: str = "#ff00ff",
        emote_assets: Path = EMOTE_IMAGE_DIR,
        ui_images: IconImages | None = None,
    ) -> None:
        self._root = root
        self._anchor = anchor
        self._font_name = font_name
        self._always_on_top = always_on_top
        self._restore_stack = restore_stack
        self._transparent_color = transparent_color
        self._emote_assets = emote_assets
        self._ui_images = ui_images
        self.bubble: tk.Toplevel | None = None
        self._nonblocking = False
        self.pending_timer: str | None = None
        self.emote_images: dict[str, tk.PhotoImage] = {}
        self.game_hand_images: dict[Move, tk.PhotoImage] = {}
        self.attribution = ""
        self._game_mode = False
        self._game_hand: Move | None = None
        root.bind("<Destroy>", lambda event: (
            self.release_images() if event.widget is root else None
        ), add="+")

    @property
    def blocks_contact(self) -> bool:
        return self.bubble is not None and not self._nonblocking

    def show_cursor_emote(self, emote: str, duration_ms: int) -> None:
        """Use a vacant speech slot without acquiring an interaction lock."""
        if self.bubble is not None:
            return
        self.show_emote(emote, duration_ms)
        self._nonblocking = True

    def show_cursor_warning(self, text: str, duration_ms: int) -> bool:
        """Report actual vacant-slot presentation, with contact still available."""
        if self.bubble is not None:
            return False
        self.show_text(text, duration_ms)
        self._nonblocking = True
        return self.bubble is not None

    def release_images(self) -> None:
        """Release cached images at root destruction on Tk's owner thread."""
        self.emote_images.clear()
        self.game_hand_images.clear()

    def _new_window(self) -> tk.Toplevel:
        window = tk.Toplevel(self._root)
        window.withdraw()
        window.overrideredirect(True)
        transparent = self._transparent_color if sys.platform == "win32" else "#202733"
        window.configure(bg=transparent)
        window.wm_attributes("-topmost", self._always_on_top())
        if sys.platform == "win32":
            window.wm_attributes("-toolwindow", True)
            window.wm_attributes("-transparentcolor", self._transparent_color)
        return window

    def set_topmost(self, enabled: bool) -> None:
        """Apply the user's stacking preference to the active bubble."""
        if self.bubble is not None:
            self.bubble.wm_attributes("-topmost", enabled)

    def move(self) -> None:
        """Place speech above Aiko's head, never above the hover toolbar."""
        bubble = self.bubble
        if bubble is None:
            return
        bubble.update_idletasks()
        width = bubble.winfo_reqwidth()
        height = bubble.winfo_reqheight()
        screen_width = self._root.winfo_screenwidth()
        screen_height = self._root.winfo_screenheight()
        anchor = self._anchor()
        x = anchor.x + (anchor.width - width) // 2
        y = anchor.y - height - 7
        if y < 0:
            y = anchor.y + 4
            x = anchor.x + anchor.width + 5
            if x + width > screen_width:
                x = anchor.x - width - 5
        x = max(0, min(x, max(0, screen_width - width)))
        y = max(0, min(y, max(0, screen_height - height)))
        bubble.geometry(f"+{x}+{y}")

    def _present(self, window: tk.Toplevel, duration_ms: int) -> None:
        self.bubble = window
        self.move()
        window.deiconify()
        self._restore_stack()
        if duration_ms > 0:
            self.pending_timer = self._root.after(duration_ms, self._expire)

    def _expire(self) -> None:
        self.pending_timer = None
        if self._game_mode and self._game_hand is not None:
            self._show_game_content("", None, 0)
        elif self._game_mode:
            self._dismiss_window()
        else:
            self.hide()

    def begin_game(self) -> None:
        self.hide()
        self._game_mode = True

    def clear_game_hand(self) -> None:
        self._game_hand = None
        self._dismiss_window()

    def _show_game_content(
        self, text: str, emote: str | None, duration_ms: int,
    ) -> None:
        """One stable surface: exclusive comment above a persistent own hand."""
        self._dismiss_window()
        bubble = self._new_window()
        transparent = self._transparent_color if sys.platform == "win32" else "#202733"
        surface = RoundedPanel(
            bubble, fill="#FFFCFD", border="#B8CDDF", background=transparent,
        )
        surface.frame.pack()
        comment = tk.Frame(surface.body, width=250, height=90, bg="#FFFCFD")
        comment.pack()
        comment.pack_propagate(False)
        if emote is not None:
            if emote not in self.emote_images:
                path = self._emote_assets / f"emote_{emote}.png"
                self.emote_images[emote] = tk.PhotoImage(
                    master=self._root, file=str(path),
                ).zoom(3)
            tk.Label(comment, image=self.emote_images[emote], bg="#FFFCFD").pack(
                expand=True,
            )
        else:
            tk.Label(
                comment, text=text, wraplength=230, justify="center", bg="#FFFCFD",
                fg="#3E4C61", font=(self._font_name, 10),
            ).pack(expand=True)
        if self._game_hand is not None:
            move = self._game_hand
            if move not in self.game_hand_images:
                if self._ui_images is None:
                    self._ui_images = IconImages(self._root)
                self.game_hand_images[move] = self._ui_images.icon(
                    f"play_rps_{move.value}", 96,
                )
            tk.Label(
                surface.body, image=self.game_hand_images[move], bg="#FFFCFD",
            ).pack()
            tk.Label(
                surface.body, text=GERMAN_TEXT.format(f"rps.move.{move.value}"),
                font=(self._font_name, 9), bg="#FFFCFD", fg="#65758A",
            ).pack()
        self._present(bubble, duration_ms)

    def show_emote(self, emote: str, duration_ms: int = 900) -> None:
        """Display one hand-authored icon in the same position as speech."""
        if emote not in EMOTES:
            raise ValueError(f"Unsupported emote: {emote}")
        if self._game_mode:
            self._show_game_content("", emote, duration_ms)
            return
        self.hide()
        bubble = self._new_window()
        if emote not in self.emote_images:
            path = self._emote_assets / f"emote_{emote}.png"
            if not path.is_file():
                bubble.destroy()
                raise FileNotFoundError(f"Missing emote: {path}")
            original = tk.PhotoImage(file=str(path))
            self.emote_images[emote] = original.zoom(3)
        transparent = self._transparent_color if sys.platform == "win32" else "#202733"
        tk.Label(
            bubble,
            image=self.emote_images[emote],
            bg=transparent,
            borderwidth=0,
            highlightthickness=0,
        ).pack()
        self._present(bubble, duration_ms)

    def show_text(self, phrase: str, duration_ms: int = 1800) -> None:
        """Show plain text, never HTML or executable message contents."""
        if self._game_mode:
            self._show_game_content(phrase, None, duration_ms)
            return
        self.hide()
        bubble = self._new_window()
        frame = tk.Frame(bubble, bg="#53687e", bd=0)
        frame.pack()
        tk.Label(
            frame,
            text=phrase,
            font=(self._font_name, 9),
            wraplength=235,
            bg="#f0f6fa",
            fg="#243247",
            justify="center",
            padx=12,
            pady=8,
        ).pack(padx=1, pady=1)
        if self.attribution:
            tk.Label(
                frame, text=self.attribution, font=(self._font_name, 7),
                wraplength=235, bg="#f0f6fa", fg="#243247", justify="center",
                padx=8, pady=4,
            ).pack(padx=1, pady=(0, 1))
        transparent = self._transparent_color if sys.platform == "win32" else "#202733"
        tail = tk.Canvas(
            bubble,
            width=20,
            height=11,
            bg=transparent,
            highlightthickness=0,
            borderwidth=0,
        )
        tail.pack()
        tail.create_polygon(
            2,
            0,
            18,
            0,
            10,
            10,
            fill="#f0f6fa",
            outline="#53687e",
            width=1,
        )
        self._present(bubble, duration_ms)

    def show_game_hand(
        self,
        aiko: Move,
        duration_ms: int = 2300,
    ) -> None:
        """Show only Aiko's own hand in the existing character bubble."""
        if not isinstance(aiko, Move):
            raise ValueError("Unknown game hand")
        if self._game_mode:
            self._game_hand = aiko
            self._show_game_content("", None, duration_ms)
            return
        if aiko not in self.game_hand_images:
            if self._ui_images is None:
                self._ui_images = IconImages(self._root)
            self.game_hand_images[aiko] = self._ui_images.icon(
                f"play_rps_{aiko.value}", 64,
            )
        self.hide()
        bubble = self._new_window()
        transparent = self._transparent_color if sys.platform == "win32" else "#202733"
        surface = RoundedPanel(
            bubble, fill="#FFFCFD", border="#B8CDDF", background=transparent,
        )
        surface.frame.pack()
        panel = surface.body
        names = {
            Move.ROCK: GERMAN_TEXT.format("rps.move.rock"),
            Move.PAPER: GERMAN_TEXT.format("rps.move.paper"),
            Move.SCISSORS: GERMAN_TEXT.format("rps.move.scissors"),
        }
        tk.Label(
            panel,
            text=GERMAN_TEXT.format("rps.choose_own_hand"),
            bg="#FFFCFD",
            fg="#3E4C61",
            font=("Segoe UI", 9, "bold"),
        ).pack(padx=12, pady=(8, 1))
        tk.Label(
            panel,
            image=self.game_hand_images[aiko],
            bg="#FFFCFD",
            bd=0,
            highlightthickness=0,
        ).pack(padx=8)
        tk.Label(
            panel,
            text=names[aiko],
            bg="#FFFCFD",
            fg="#3E4C61",
            font=("Segoe UI", 9),
        ).pack(padx=12, pady=(1, 8))
        tail = tk.Canvas(
            bubble,
            width=20,
            height=11,
            bg=transparent,
            highlightthickness=0,
            borderwidth=0,
        )
        tail.pack()
        tail.create_polygon(
            2,
            0,
            18,
            0,
            10,
            10,
            fill="#FFFCFD",
            outline="#B8CDDF",
            width=1,
        )
        self._present(bubble, duration_ms)

    def hide(self) -> None:
        """Cancel the old timeout so a previous bubble cannot hide a new one."""
        self._game_mode = False
        self._game_hand = None
        self._dismiss_window()

    def _dismiss_window(self) -> None:
        self._nonblocking = False
        if self.pending_timer is not None:
            self._root.after_cancel(self.pending_timer)
            self.pending_timer = None
        if self.bubble is not None:
            self.bubble.destroy()
            self.bubble = None
