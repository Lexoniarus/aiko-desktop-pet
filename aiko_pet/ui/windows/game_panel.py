"""Shared VN player window; sequences retain their existing state and timers."""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable

from ...asset_paths import GAME_ART_DIR, PLAYING_CARDS_DIR
from ...games.contracts import GameId, SessionSummary
from ...pet.content import GERMAN_TEXT
from ..common import scaled_widgets as scaled
from ..common.content_region import ContentRegion
from ..common.image_button import ImageButton, update_button_state
from ..common.rounded_panel import RoundedPanel
from ..common.skin import AikoSkin
from ..common.window_drag import WindowDrag
from ..common.window_geometry import BoundsAt, WindowBounds, beside_character


class GamePanel:
    def __init__(
        self, root: tk.Tk, title: str, *, close: Callable[[], None],
        next_round: Callable[[], None] | None, skin: AikoSkin, always_on_top: bool,
        game_id: GameId, bounds_at: BoundsAt | None = None,
        reserve_right: int = 0,
    ) -> None:
        self.skin = skin
        self._reserve_right = reserve_right
        self._bounds_at = bounds_at or (lambda _x, _y: WindowBounds(
            0, 0, root.winfo_screenwidth(), root.winfo_screenheight(),
        ))
        self.width = 548
        self.content_width = self.width - 36
        self._placed = False
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg=skin.border)
        self.window.wm_attributes('-topmost', always_on_top)
        if sys.platform == 'win32':
            self.window.wm_attributes('-toolwindow', True)
        self.window.protocol('WM_DELETE_WINDOW', close)
        self.window.bind('<Escape>', lambda _event: close())
        outer = scaled.Frame(self.window, bg=skin.background)
        outer.pack(fill='both', expand=True, padx=1, pady=1)
        header = scaled.Frame(outer, bg=skin.title)
        header.pack(fill='x')
        icon = (
            skin.images.file(PLAYING_CARDS_DIR / 'card_spades_A.png', 32)
            if game_id is GameId.BLACKJACK
            else skin.images.file(GAME_ART_DIR / 'c4-red.png', 32)
            if game_id is GameId.CONNECT_FOUR
            else skin.images.file(GAME_ART_DIR / 'mm-blue.png', 32)
            if game_id is GameId.MASTERMIND
            else skin.images.file(GAME_ART_DIR / 'quiz-emblem.png', 32)
            if game_id is GameId.QUIZ
            else skin.images.icon(
                'game_rps' if game_id is GameId.ROCK_PAPER_SCISSORS
                else 'game_tic_tac_toe', 32,
            )
        )
        emblem = scaled.Label(header, image=icon, bg=skin.title)
        emblem.pack(side='left', padx=(14, 8))
        self.header_close = skin.button(header, '×', close, size='small')
        self.header_close.pack(side='right', padx=(4, 12), pady=8)
        copy = scaled.Frame(header, bg=skin.title)
        copy.pack(side='left', fill='both', expand=True, pady=8)
        brand = scaled.Label(
            copy, text=GERMAN_TEXT.format('game.brand'), bg=skin.title,
            fg=skin.muted, font=(skin.font, 8), anchor='w',
        )
        brand.pack(fill='x')
        self.title = scaled.Label(
            copy, text=title, bg=skin.title, fg=skin.text,
            font=(skin.font, 12, 'bold'), anchor='w',
            wraplength=max(90, self.width - 130), justify='left',
        )
        self.title.pack(fill='x')
        self._drag = WindowDrag(
            self.window, header, handles=(emblem, copy, brand, self.title),
            bounds_at=self._bounds_at,
        )
        footer = scaled.Frame(outer, bg=skin.background)
        footer.pack(side='bottom', fill='x', padx=16, pady=12)
        footer.grid_columnconfigure(0, weight=1)
        self.close_button = skin.button(
            footer, GERMAN_TEXT.format('ui.close'), close, size='game_close',
        )
        self.close_button.grid(row=0, column=1, sticky='e')
        self.next_button: ImageButton | None = None
        if next_round is not None:
            self.next_button = skin.button(
                footer, GERMAN_TEXT.format('game.next'), next_round, size='game_next',
            )
            self.next_button.configure(state='disabled')
            self.next_button.grid(row=0, column=0, sticky='w', padx=(0, 8))
        else:
            scaled.Label(
                footer, text=GERMAN_TEXT.format(
                    'game.rps_again' if game_id is GameId.ROCK_PAPER_SCISSORS
                    else 'game.blackjack_again'
                ), bg=skin.background, fg=skin.muted, font=(skin.font, 8),
                wraplength=max(60, self.width - 210), justify='left', anchor='w',
            ).grid(row=0, column=0, sticky='w', padx=(0, 8))
        scores = scaled.Frame(outer, bg=skin.background)
        scores.pack(side='bottom', fill='x', padx=16)
        self.score_labels: dict[str, tk.Label] = {}
        score_columns = (("correct", "correct"), ("answered", "answered")) if (
            game_id is GameId.QUIZ
        ) else (
            ('wins', 'player'), ('losses', 'aiko'),
            ('draws', 'draws'), ('games', 'rounds'),
        )
        for col, (key, label) in enumerate(score_columns):
            scores.grid_columnconfigure(col, weight=1, uniform='scores')
            cell = self.passive(scores, padding=6)
            cell.frame.grid(row=0, column=col, sticky='nsew', padx=3)
            scaled.Label(
                cell.body, text=GERMAN_TEXT.format(f'game.score.{label}'),
                bg=skin.panel, fg=skin.muted, font=(skin.font, 8),
            ).pack()
            count = scaled.Label(
                cell.body, text='0', bg=skin.panel,
                fg=skin.text, font=(skin.font, 14, 'bold'),
            )
            count.pack()
            self.score_labels[key] = count
        self._status_surface = self.passive(outer)
        self._status_surface.frame.pack(
            side='bottom', fill='x', padx=16, pady=(8, 10),
        )
        self.status = scaled.Label(
            self._status_surface.body, bg=skin.panel, fg=skin.text,
            font=(skin.font, 9), anchor='w', justify='left',
            wraplength=self.content_width - 24,
        )
        self.status.pack(fill='x')
        self.content = ContentRegion(
            outer, skin,
        )
        self.content.frame.pack(fill='both', expand=True, padx=16, pady=(12, 0))
        self.body = self.content.body

    def passive(self, parent: tk.Misc, *, padding: int = 10) -> RoundedPanel:
        return RoundedPanel(
            parent, fill=self.skin.panel, border=self.skin.border,
            background=self.skin.background, padding=padding,
        )

    def show(self, root: tk.Tk) -> None:
        if not self._placed:
            self.window.update_idletasks()
            bounds = self._bounds_at(
                root.winfo_rootx() + root.winfo_width() // 2,
                root.winfo_rooty() + root.winfo_height() // 2,
            )
            width = max(
                self.skin.scale.pixels(self.width), self.window.winfo_reqwidth(),
            )
            height = self.window.winfo_reqheight()
            x, y = beside_character(
                root.winfo_rootx(), root.winfo_rooty(),
                root.winfo_width() + self._reserve_right, root.winfo_height(),
                width, height, bounds,
            )
            self.window.minsize(self.skin.scale.pixels(self.width), 1)
            self.window.geometry(f'+{x}+{y}')
            self.window.bind('<Configure>', self._keep_in_bounds, add='+')
            self._placed = True
        self.window.deiconify()

    def _keep_in_bounds(self, event: tk.Event) -> None:
        if event.widget is not self.window:
            return
        bounds = self._bounds_at(self.window.winfo_x(), self.window.winfo_y())
        x, y = bounds.clamp(
            self.window.winfo_x(), self.window.winfo_y(),
            self.window.winfo_width(), self.window.winfo_height(),
        )
        if (x, y) != (self.window.winfo_x(), self.window.winfo_y()):
            self.window.geometry(f'+{x}+{y}')

    def update(self, score: SessionSummary, *, status: str, finished: bool) -> None:
        color = '#F8EAF1' if finished else self.skin.panel
        self._status_surface.set_fill(color)
        self.status.configure(text=status, bg=color)
        for key, label in self.score_labels.items():
            label.configure(text=str(getattr(score, key)))
        if self.next_button is not None:
            update_button_state(self.next_button, enabled=finished)

    def destroy(self) -> None:
        self._drag.close()
        self.window.destroy()
