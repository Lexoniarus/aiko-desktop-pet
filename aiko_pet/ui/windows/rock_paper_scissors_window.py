"""VN player choices and revealed hand; Aiko's presentation stays on the desktop."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from functools import partial

from ...games.contracts import GameId, GameRoundEvent, SessionSummary
from ...games.rock_paper_scissors import Move, Score
from ...pet.content import GERMAN_TEXT
from ..common.image_button import ImageButton, update_button_state
from ..common.scroll_region import ScrollRegion
from ..common.skin import AikoSkin
from ..common.window_geometry import BoundsAt
from .game_panel import GamePanel
from .rock_paper_scissors_sequence import RockPaperScissorsSequence

_MOVES: tuple[tuple[Move, str], ...] = (
    (Move.ROCK, GERMAN_TEXT.format('rps.move.rock')),
    (Move.PAPER, GERMAN_TEXT.format('rps.move.paper')),
    (Move.SCISSORS, GERMAN_TEXT.format('rps.move.scissors')),
)
_MOVE_NAMES = dict(_MOVES)


class RockPaperScissorsWindow:
    def __init__(
        self, root: tk.Tk, *, on_closed: Callable[[SessionSummary], None],
        speak: Callable[[str, int], None], emote: Callable[[str, int], None],
        hand: Callable[[Move, int], None], animate: Callable[[str], None],
        always_on_top: bool, skin: AikoSkin | None = None,
        dialogue: Callable[[str], str] | None = None,
        round_event: Callable[[GameRoundEvent], None] = lambda _event: None,
        express_event: Callable[[str], None] = lambda _event: None,
        bounds_at: BoundsAt | None = None,
    ) -> None:
        self._on_closed = on_closed
        self._closed = False
        self.skin = skin if skin is not None else AikoSkin(root)
        self._panel = GamePanel(
            root, GERMAN_TEXT.format('game.name.rock_paper_scissors'),
            close=self.close, next_round=None, skin=self.skin,
            always_on_top=always_on_top, game_id=GameId.ROCK_PAPER_SCISSORS,
            bounds_at=bounds_at,
        )
        self.window = self._panel.window
        try:
            self.hand_images = {
                move: self.skin.images.icon(f'play_rps_{move.value}', 96)
                for move, _label in _MOVES
            }
            self._last_revealed: Move | None = None
            self._shown_score = Score()
            tk.Label(
                self._panel.body, text=GERMAN_TEXT.format('rps.choose_hand'),
                bg=self.skin.background, fg=self.skin.text,
                font=(self.skin.font, 10, 'bold'), anchor='w',
            ).pack(fill='x', pady=(0, 8))
            self._choices_scroll = ScrollRegion(
                self._panel.body, self.skin, width=self._panel.content_width,
                height=116, horizontal=True, autohide=True,
            )
            self._choices_scroll.frame.pack(fill='x')
            choices = self._choices_scroll.body
            self.buttons: dict[Move, ImageButton] = {}
            for move, label in _MOVES:
                button = self.skin.button(
                    choices, label, partial(self.choose, move), size='game_choice',
                    icon=self.skin.images.icon(f'play_rps_{move.value}', 64),
                    stacked=True,
                )
                button.pack(side='left', padx=2)
                self.buttons[move] = button
            self._choices_scroll.adopt()
            self._hand_panel = self._panel.passive(self._panel.body)
            self.result_panel = self._hand_panel.frame
            self.result_panel.pack(fill='x', pady=(12, 0))
            body = self._hand_panel.body
            self.result_title = tk.Label(
                body, text=GERMAN_TEXT.format('rps.your_hand'), bg=self.skin.panel,
                fg=self.skin.muted, font=(self.skin.font, 9),
            )
            self.result_title.pack()
            self.player_hand = tk.Canvas(
                body, width=120, height=96, bg=self.skin.panel,
                bd=0, highlightthickness=0,
            )
            self.player_hand.pack()
            self._hand_image_item = self.player_hand.create_image(
                60, 48, anchor='center', state='hidden',
            )
            self._hand_question_item = self.player_hand.create_text(
                60, 48, text='?', fill=self.skin.muted,
                font=(self.skin.font, 22),
            )
            self.player_result_label = tk.Label(
                body, text=GERMAN_TEXT.format('rps.no_rounds'), bg=self.skin.panel,
                fg=self.skin.muted, font=(self.skin.font, 9),
            )
            self.player_result_label.pack()
            self.score_labels = self._panel.score_labels
            self.close_button = self._panel.close_button
            self._sequence = RockPaperScissorsSequence(
                dialogue=dialogue, round_event=round_event,
                express_event=express_event,
                schedule=self.window.after, cancel=self.window.after_cancel,
                say=speak, show_emote=emote, show_aiko_hand=hand,
                reveal_player=self.reveal_player, animate=animate,
                set_busy=self._set_busy,
            )
            self._panel.update(
                SessionSummary(GameId.ROCK_PAPER_SCISSORS),
                status=GERMAN_TEXT.format('rps.choose_hand'), finished=False,
            )
            self._panel.show(root)
        except Exception:
            self._closed = True
            self._panel.destroy()
            raise

    @property
    def score(self) -> Score:
        return self._sequence.score

    def greet(self) -> None:
        self._sequence.greet()

    def _set_busy(self, busy: bool) -> None:
        for button in self.buttons.values():
            update_button_state(button, enabled=not busy)
        if busy:
            self._panel.update(
                SessionSummary(
                    GameId.ROCK_PAPER_SCISSORS,
                    self.score.wins, self.score.losses, self.score.draws,
                ), status=GERMAN_TEXT.format('rps.waiting'), finished=False,
            )

    def _clear_player_result(self) -> None:
        self.player_result_label.configure(text=GERMAN_TEXT.format(
            'rps.waiting' if self._last_revealed is None else 'rps.previous_hand',
            hand=_MOVE_NAMES[self._last_revealed] if self._last_revealed else '',
        ))

    def reveal_player(self, move: Move, score: Score) -> None:
        self._last_revealed = move
        self.player_hand.itemconfigure(
            self._hand_image_item, image=self.hand_images[move], state='normal',
        )
        self.player_hand.itemconfigure(self._hand_question_item, state='hidden')
        self.player_result_label.configure(text=GERMAN_TEXT.format(
            'rps.player_hand', hand=_MOVE_NAMES[move],
        ))
        result = (
            'game.player_win' if score.wins > self._shown_score.wins
            else 'game.aiko_win' if score.losses > self._shown_score.losses
            else 'game.draw'
        )
        self._shown_score = score
        self._panel.update(
            SessionSummary(
                GameId.ROCK_PAPER_SCISSORS, score.wins, score.losses, score.draws,
            ),
            status=GERMAN_TEXT.format(result), finished=True,
        )

    def choose(self, move: Move) -> None:
        if not self._closed and not self._sequence.busy:
            self._clear_player_result()
            self._sequence.choose(move)

    def focus(self) -> None:
        self.window.deiconify()
        self.window.lift()
        self.window.focus_set()

    def set_topmost(self, enabled: bool) -> None:
        self.window.wm_attributes('-topmost', enabled)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        completed = self._sequence.score
        self._sequence.close()
        self._panel.destroy()
        self._on_closed(SessionSummary(
            GameId.ROCK_PAPER_SCISSORS,
            completed.wins, completed.losses, completed.draws,
        ))
