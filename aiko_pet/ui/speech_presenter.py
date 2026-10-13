"""Tk speech and emote display, independent of application/domain decisions."""

from __future__ import annotations

import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..asset_paths import EMOTE_ASSETS, GAME_HANDS_DIR
from ..games.rock_paper_scissors import Move
from ..personality.reaction_sequence import EMOTES


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
        emote_assets: Path = EMOTE_ASSETS,
    ) -> None:
        self._root = root
        self._anchor = anchor
        self._font_name = font_name
        self._always_on_top = always_on_top
        self._restore_stack = restore_stack
        self._transparent_color = transparent_color
        self._emote_assets = emote_assets
        self.bubble: tk.Toplevel | None = None
        self.pending_timer: str | None = None
        self.emote_images: dict[str, tk.PhotoImage] = {}
        self.game_hand_images: dict[Move, tk.PhotoImage] = {}

    def _new_window(self) -> tk.Toplevel:
        window = tk.Toplevel(self._root)
        window.withdraw()
        window.overrideredirect(True)
        transparent = (
            self._transparent_color if sys.platform == "win32" else "#202733"
        )
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
        self.pending_timer = self._root.after(duration_ms, self.hide)

    def show_emote(self, emote: str, duration_ms: int = 900) -> None:
        """Display one hand-authored icon in the same position as speech."""
        if emote not in EMOTES:
            raise ValueError(f"Unsupported emote: {emote}")
        self.hide()
        bubble = self._new_window()
        if emote not in self.emote_images:
            path = self._emote_assets / f"emote_{emote}.png"
            if not path.is_file():
                bubble.destroy()
                raise FileNotFoundError(f"Missing emote: {path}")
            original = tk.PhotoImage(file=str(path))
            self.emote_images[emote] = original.zoom(3)
        transparent = (
            self._transparent_color if sys.platform == "win32" else "#202733"
        )
        tk.Label(
            bubble, image=self.emote_images[emote],
            bg=transparent, borderwidth=0, highlightthickness=0,
        ).pack()
        self._present(bubble, duration_ms)

    def show_text(self, phrase: str, duration_ms: int = 1800) -> None:
        """Show plain text, never HTML or executable message contents."""
        self.hide()
        bubble = self._new_window()
        frame = tk.Frame(bubble, bg="#53687e", bd=0)
        frame.pack()
        tk.Label(
            frame, text=phrase, font=(self._font_name, 9), wraplength=235,
            bg="#f0f6fa", fg="#243247", justify="center",
            padx=12, pady=8,
        ).pack(padx=1, pady=1)
        transparent = (
            self._transparent_color if sys.platform == "win32" else "#202733"
        )
        tail = tk.Canvas(
            bubble, width=20, height=11, bg=transparent,
            highlightthickness=0, borderwidth=0,
        )
        tail.pack()
        tail.create_polygon(
            2, 0, 18, 0, 10, 10, fill="#f0f6fa",
            outline="#53687e", width=1,
        )
        self._present(bubble, duration_ms)

    def show_game_hands(
        self, player: Move, aiko: Move, duration_ms: int = 2000,
    ) -> None:
        """Reveal both color hand images in Aiko's established speech bubble."""
        if not isinstance(player, Move) or not isinstance(aiko, Move):
            raise ValueError("Unknown game hand")
        for move in (player, aiko):
            if move not in self.game_hand_images:
                self.game_hand_images[move] = tk.PhotoImage(
                    file=str(GAME_HANDS_DIR / f"{move.value}.png"),
                )
        self.hide()
        bubble = self._new_window()
        frame = tk.Frame(bubble, bg="#53687e", bd=0)
        frame.pack()
        panel = tk.Frame(frame, bg="#f0f6fa")
        panel.pack(padx=1, pady=1)
        tk.Label(
            panel, text="Und ... aufgedeckt!", bg="#f0f6fa", fg="#243247",
            font=(self._font_name, 9, "bold"),
        ).pack(padx=8, pady=(8, 2))
        hands = tk.Frame(panel, bg="#f0f6fa")
        hands.pack(padx=8, pady=(0, 8))
        labels = {Move.ROCK: "Stein", Move.PAPER: "Papier",
                  Move.SCISSORS: "Schere"}
        for column, (title, move) in enumerate((("Du", player), ("Ich", aiko))):
            cell = tk.Frame(hands, bg="#f0f6fa")
            cell.grid(row=0, column=column, padx=10)
            tk.Label(
                cell, text=title, bg="#f0f6fa", fg="#243247",
                font=(self._font_name, 9, "bold"),
            ).pack()
            tk.Label(
                cell, image=self.game_hand_images[move], bg="#f0f6fa",
                bd=0, highlightthickness=0,
            ).pack()
            tk.Label(
                cell, text=labels[move], bg="#f0f6fa", fg="#243247",
                font=(self._font_name, 9),
            ).pack()
        transparent = (
            self._transparent_color if sys.platform == "win32" else "#202733"
        )
        tail = tk.Canvas(
            bubble, width=20, height=11, bg=transparent,
            highlightthickness=0, borderwidth=0,
        )
        tail.pack()
        tail.create_polygon(
            2, 0, 18, 0, 10, 10, fill="#f0f6fa",
            outline="#53687e", width=1,
        )
        self._present(bubble, duration_ms)

    def hide(self) -> None:
        """Cancel the old timeout so a previous bubble cannot hide a new one."""
        if self.pending_timer is not None:
            self._root.after_cancel(self.pending_timer)
            self.pending_timer = None
        if self.bubble is not None:
            self.bubble.destroy()
            self.bubble = None
