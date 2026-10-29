"""Player cards and decisions; Aiko's hand belongs only to the desktop."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Literal

from ...games.blackjack import Phase, Table
from ...games.contracts import GameId, GameRoundEvent, SessionSummary
from ...pet.content import GERMAN_TEXT
from ..common.scroll_region import ScrollRegion
from ..common.skin import AikoSkin
from ..common.window_geometry import BoundsAt
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
        round_event: Callable[[GameRoundEvent], None] = lambda _event: None,
        express_event: Callable[[str], None] = lambda _event: None,
        bounds_at: BoundsAt | None = None,
    ) -> None:
        self._closed = False
        self._on_closed, self._cards = on_closed, cards
        self.skin = skin
        self._panel = GamePanel(
            root, GERMAN_TEXT.format("game.name.blackjack"), close=self.close,
            next_round=None, skin=skin, always_on_top=always_on_top,
            game_id=GameId.BLACKJACK, bounds_at=bounds_at, body_height=384,
        )
        self.window = self._panel.window
        try:
            heading = tk.Frame(self._panel.body, bg=skin.background)
            heading.pack(fill="x", pady=(0, 4))
            tk.Label(
                heading, text=GERMAN_TEXT.format("game.hand"), bg=skin.background,
                fg=skin.text, font=(skin.font, 10, "bold"),
            ).pack(side="left")
            total_panel = self._panel.passive(heading, padding=5)
            total_panel.frame.pack(side="right")
            self.total = tk.Label(
                total_panel.body, bg=skin.panel, fg=skin.text, font=(skin.font, 9),
            )
            self.total.pack()
            self._hand_scroll = ScrollRegion(
                self._panel.body, skin,
                width=min(self.HAND_WIDTH, self._panel.content_width), height=144,
                horizontal=True, autohide=True,
            )
            self._hand_scroll.frame.pack()
            self.player_cards = tk.Canvas(
                self._hand_scroll.body, width=self.HAND_WIDTH, height=144,
                bg=skin.background,
                bd=0, highlightthickness=0,
            )
            self.player_cards.pack()
            controls = tk.Frame(self._panel.body, bg=skin.background)
            controls.pack(pady=3)
            self.hit_button = tk.Button(
                controls, text=GERMAN_TEXT.format("blackjack.hit"),
                image=cards.images.draw_pile(self.PLAYER_CARD_SCALE),
                compound="top", command=self.hit, font=(skin.font, 10),
                bg="#FAEDF3", fg=skin.text, padx=10, pady=6,
                activebackground="#F5DEEA", activeforeground=skin.text,
                disabledforeground=skin.muted, bd=0, relief="flat",
                highlightthickness=1, highlightbackground="#C99BB1",
                highlightcolor=skin.accent, cursor="hand2",
            )
            self.hit_button.pack(side="left", padx=(0, 20))
            self.stand_button = skin.button(
                controls, GERMAN_TEXT.format("blackjack.stand"), self.stand,
                size="game_stand",
            )
            self.stand_button.pack(side="left")
            if self._panel.content_width < 360:
                self.hit_button.pack_configure(side="top", padx=0, pady=(0, 8))
                self.stand_button.pack_configure(side="top")
            self._sequence = BlackjackSequence(
                schedule=self.window.after, cancel=self.window.after_cancel,
                present=self._present, hand=cards.show, say=speak,
                animate=animate, dialogue=dialogue,
                round_event=round_event,
                express_event=express_event,
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
