"""Player cards and decisions; Aiko's hand belongs only to the desktop."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Literal

from ...asset_paths import GAME_ART_DIR
from ...games.blackjack import Phase, Table
from ...games.contracts import GameId, GameRoundEvent, SessionSummary
from ...pet.content import GERMAN_TEXT
from ..common.scroll_region import ScrollRegion
from ..common.skin import AikoSkin
from ..common.window_geometry import BoundsAt
from .blackjack_motion import BlackjackMotion
from .blackjack_sequence import BlackjackSequence
from .game_contracts import GameCardPorts
from .game_panel import GamePanel
from .game_presentation import GamePresentation
from .game_waiting import GameWaiting


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
        presentation: GamePresentation | None = None,
        emote: Callable[[str, int], None] = lambda _name, _ms: None,
    ) -> None:
        self._closed = False
        self._on_closed, self._cards = on_closed, cards
        self.skin = skin
        self._motion: BlackjackMotion | None = None
        self._visible = Table((), (), 0, Phase.PLAYER, None)
        self._panel = GamePanel(
            root, GERMAN_TEXT.format("game.name.blackjack"), close=self.close,
            next_round=None, skin=skin, always_on_top=always_on_top,
            game_id=GameId.BLACKJACK, bounds_at=bounds_at, body_height=430,
            reserve_right=310,
        )
        self.window = self._panel.window
        self._waiting = GameWaiting(
            self.window.after, self.window.after_cancel, presentation,
            lambda: self._player_point(0, 1),
            lambda: speak("Noch eine Karte, VIP-Gast? "
                          "Ich kann auch sehr feierlich warten.", 3500),
        )
        try:
            heading = tk.Frame(self._panel.body, bg=skin.background)
            heading.pack(fill="x", pady=(0, 4))
            tk.Label(
                heading, text=GERMAN_TEXT.format("game.frontend.blackjack"),
                bg=skin.background,
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
            self.hit_button = skin.button(
                controls, GERMAN_TEXT.format("blackjack.hit") + "  [Z]",
                self.hit, size="game_stand",
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
            self._felt = tk.PhotoImage(master=self.window,
                                       file=str(GAME_ART_DIR / 'blackjack-table.png'))
            self.player_cards.configure(height=280, bg="#faedf3")
            self._hand_scroll.canvas.configure(height=280)
            if presentation is not None:
                self._motion = BlackjackMotion(
                    self.window, cards, presentation, self._player_point,
                    lambda: self._visible, lambda: self.player_cards.delete("all"),
                    self.hit,
                    topmost=always_on_top,
                )
            self.window.bind("z", lambda _: self.hit())
            self.window.bind("b", lambda _: self.stand())
            self._sequence = BlackjackSequence(
                schedule=self.window.after, cancel=self.window.after_cancel,
                present=self._present, hand=cards.show, say=speak,
                animate=animate, dialogue=dialogue,
                round_event=round_event,
                express_event=express_event,
                motion=self._motion.play if self._motion else None, emote=emote,
            )
            self._present(self._sequence.game.table, self._sequence.game.score)
            self._panel.show(root)
        except Exception:
            if self._motion is not None:
                self._motion.close()
            self._panel.destroy()
            raise

    def greet(self) -> None:
        self._sequence.greet()

    def _player_point(self, index: int, count: int) -> tuple[float, float]:
        step = min(92, (self.HAND_WIDTH - 144) // max(1, count - 1))
        left = (self.HAND_WIDTH - 128 - (count - 1) * step) // 2
        return (self.player_cards.winfo_rootx() + left + index * step,
                self.player_cards.winfo_rooty() + 70)

    def _present(self, table: Table, score: SessionSummary) -> None:
        self._visible = table
        self._waiting.set_active(not self._sequence.busy)
        self.player_cards.delete("all")
        self.player_cards.create_image(0, 0, anchor="nw", image=self._felt,
                                       tags="felt")
        self.player_cards.create_text(240, 36, text="BLACKJACK", fill="#f9edcc",
                                      font=(self.skin.font, 13, "bold"))
        width = 64 * self.PLAYER_CARD_SCALE
        step = min(92, (self.HAND_WIDTH - width - 16)
                   // max(1, len(table.player) - 1))
        left = (self.HAND_WIDTH - width - (len(table.player) - 1) * step) // 2
        for i, card in enumerate(table.player):
            self.player_cards.create_image(
                left + width // 2 + i * step, 134,
                image=self._cards.images.get(card, self.PLAYER_CARD_SCALE),
            )
        self.total.configure(text=GERMAN_TEXT.format(
            "blackjack.total", total=str(table.player_total),
        ))
        state: Literal["normal", "disabled"] = (
            "normal" if table.phase is Phase.PLAYER and not self._sequence.busy
            else "disabled"
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
        if self._motion is not None:
            self._motion.effects.set_topmost(enabled)

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._waiting.set_active(False)
            summary = self._sequence.close()
            if self._motion is not None:
                self._motion.close()
            try:
                self._panel.destroy()
            finally:
                self._on_closed(summary)
