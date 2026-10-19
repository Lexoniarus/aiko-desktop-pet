"""Player cards and decisions; Aiko's hand belongs only to the desktop."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Literal

from ...games.blackjack import Phase, Table
from ...games.contracts import SessionSummary
from ...pet.content import GERMAN_TEXT
from ..common.skin import AikoSkin
from .blackjack_sequence import BlackjackSequence
from .game_contracts import GameCardPorts
from .game_panel import GamePanel


class BlackjackWindow:
    PLAYER_CARD_SCALE = 2
    HAND_WIDTH = 480

    def __init__(
        self, root: tk.Tk, *, on_closed: Callable[[SessionSummary], None],
        cards: GameCardPorts, speak: Callable[[str, int], None],
        animate: Callable[[str], None], always_on_top: bool, skin: AikoSkin,
        dialogue: Callable[[str], str] | None = None,
    ) -> None:
        self._closed = False
        self._on_closed, self._cards = on_closed, cards
        self.skin = skin
        self._panel = GamePanel(
            root, GERMAN_TEXT.format("game.name.blackjack"), close=self.close,
            next_round=None, skin=skin, always_on_top=always_on_top,
        )
        self.window = self._panel.window
        try:
            self.player_cards = tk.Canvas(
                self._panel.body, width=self.HAND_WIDTH, height=144,
                bg=skin.background,
                bd=0, highlightthickness=0,
            )
            self.player_cards.pack()
            self.total = tk.Label(
                self._panel.body, bg=skin.background, fg=skin.text,
                font=(skin.font, 11),
            )
            self.total.pack(pady=6)
            controls = skin.frame(self._panel.body)
            controls.pack(pady=3)
            self.hit_button = tk.Button(
                controls, text=GERMAN_TEXT.format("blackjack.hit"),
                image=cards.images.draw_pile(self.PLAYER_CARD_SCALE),
                compound="top", command=self.hit, font=(skin.font, 10),
                bg=skin.background, fg=skin.text,
                activebackground=skin.panel, activeforeground=skin.accent,
                disabledforeground=skin.muted, bd=0, relief="flat",
                highlightthickness=1, highlightbackground=skin.border,
                highlightcolor=skin.accent, cursor="hand2",
            )
            self.hit_button.pack(side="left", padx=(0, 20))
            self.stand_button = skin.button(
                controls, GERMAN_TEXT.format("blackjack.stand"), self.stand,
            )
            self.stand_button.pack(side="left")
            self._sequence = BlackjackSequence(
                schedule=self.window.after, cancel=self.window.after_cancel,
                present=self._present, hand=cards.show, say=speak,
                animate=animate, dialogue=dialogue,
            )
            self._present(self._sequence.game.table, self._sequence.game.score)
            self._panel.show(root)
        except Exception:
            self._panel.destroy()
            raise

    def greet(self) -> None:
        self._sequence.greet()

    def _present(self, table: Table, score: SessionSummary) -> None:
        self.player_cards.delete("all")
        width = 64 * self.PLAYER_CARD_SCALE
        step = min(92, (self.HAND_WIDTH - width - 16)
                   // max(1, len(table.player) - 1))
        left = (self.HAND_WIDTH - width - (len(table.player) - 1) * step) // 2
        for i, card in enumerate(table.player):
            self.player_cards.create_image(
                left + width // 2 + i * step, 72,
                image=self._cards.images.get(card, self.PLAYER_CARD_SCALE),
            )
        self.total.configure(text=GERMAN_TEXT.format(
            "blackjack.total", total=str(table.player_total),
        ))
        state: Literal["normal", "disabled"] = (
            "normal" if table.phase is Phase.PLAYER else "disabled"
        )
        self.hit_button.configure(state=state)
        self.stand_button.configure(state=state)
        key = "game.player_turn" if table.phase is Phase.PLAYER else "game.aiko_turn"
        if table.result is not None:
            key = {
                "win": "game.player_win", "loss": "game.aiko_win", "draw": "game.draw",
            }[table.result]
        self._panel.update(
            score, status=GERMAN_TEXT.format(key), finished=table.result is not None,
        )

    def hit(self) -> None:
        if not self._closed:
            self._sequence.hit()

    def stand(self) -> None:
        if not self._closed:
            self._sequence.stand()

    def set_topmost(self, enabled: bool) -> None:
        self.window.wm_attributes("-topmost", enabled)

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            summary = self._sequence.close()
            try:
                self._panel.destroy()
            finally:
                self._on_closed(summary)
