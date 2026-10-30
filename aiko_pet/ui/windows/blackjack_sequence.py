"""One game owner; cancellable landing-based casino choreography."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from uuid import uuid4

from ...games.blackjack import Blackjack, Phase, Table, hand_total
from ...games.contracts import GameId, GameRoundEvent, SessionSummary
from ...games.playing_cards import Card
from ...pet.mind.reaction_sequence import Cue
from ..view_models.game_models import HandView
from .rock_paper_scissors_dialogue import GameDialogue

Motion = Callable[[str, Card | None, int, Callable[[], None]], None]


class BlackjackSequence:
    RESULT_PAUSE_MS = 2800

    def __init__(
        self, *, schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None], present: Callable[[Table, SessionSummary], None],
        hand: Callable[[HandView, bool], None], say: Callable[[str, int], None],
        animate: Callable[[str], None], dialogue: Callable[[str], str] | None = None,
        round_event: Callable[[GameRoundEvent], None] = lambda _: None,
        express_event: Callable[[str], None] = lambda _: None,
        game: Blackjack | None = None, motion: Motion | None = None,
        emote: Callable[[str, int], None] = lambda _name, _ms: None,
    ) -> None:
        self.game = game if game is not None else Blackjack()
        self._schedule, self._cancel = schedule, cancel
        self._present, self._hand = present, hand
        self._say, self._animate, self._emote = say, animate, emote
        self._dialogue = dialogue or GameDialogue().choose
        self._round_event, self._express_event = round_event, express_event
        self._motion = motion
        self._session_id = uuid4().hex
        self._closed = self._started = False
        self._generation = 0
        self.pending_timer: str | None = None
        self._next: Callable[[], None] | None = None
        self.busy = True
        self._player_count = self._dealer_count = 0
        self._dealer_revealed = False

    def _later(self, ms: int, action: Callable[[], None]) -> None:
        generation = self._generation

        def run() -> None:
            if self._closed or generation != self._generation:
                return
            self.pending_timer = None
            self._next = None
            action()
        self._next = run
        self.pending_timer = self._schedule(ms, run)

    def advance(self) -> None:
        """Advance the pending logical cue, useful for controlled adapters."""
        if self.pending_timer is not None and self._next is not None:
            self._cancel(self.pending_timer)
            self._next()

    def _move(
        self, kind: str, card: Card | None, index: int, done: Callable[[], None],
    ) -> None:
        generation = self._generation

        def landed() -> None:
            if not self._closed and generation == self._generation:
                done()
        if self._motion is not None:
            self._motion(kind, card, index, landed)
        else:
            self._later(620 if kind in ('player', 'dealer') else 1600, landed)

    def _line(self, event: str, done: Callable[[], None]) -> None:
        text = self._dialogue(event)
        duration = Cue.text(text).duration_ms
        self._express_event(event)
        self._say(text, duration)
        if event == "game_bj_aside":
            self._aside = text
        self._later(duration, done)

    def greet(self) -> None:
        if self._closed or self._started:
            return
        self._started = True
        self._begin()

    def _begin(self) -> None:
        self.busy = True
        self._player_count = self._dealer_count = 0
        self._dealer_revealed = False
        self._round_event(GameRoundEvent(
            GameId.BLACKJACK, self._session_id, self.game.score.games + 1,
        ))
        self._publish()
        self._line('game_bj_welcome', lambda: self._move(
            'shuffle', None, 0, lambda: self._deal(0),
        ))

    def _publish(self, flip: bool = False) -> None:
        source = self.game.table
        dealer = source.dealer[:self._dealer_count]
        if not self._dealer_revealed:
            dealer = tuple(card if i == 0 else None for i, card in enumerate(dealer))
        player = source.player[:self._player_count]
        table = replace(source, player=player, dealer=dealer,
                        player_total=hand_total(player))
        self._hand(HandView(dealer), flip)
        self._present(table, self.game.score)

    def _deal(self, position: int) -> None:
        if position == 4:
            self._continue()
            return
        kind = 'player' if position % 2 == 0 else 'dealer'
        index = position // 2
        card = (self.game.table.player if kind == 'player'
                else self.game.table.dealer)[index]

        def landed() -> None:
            if kind == 'player':
                self._player_count += 1
            else:
                self._dealer_count += 1
            self._publish()
            self._deal(position + 1)
        self._move(kind, card, index, landed)

    def hit(self) -> None:
        if self._closed or self.busy or self.game.table.phase is not Phase.PLAYER:
            return
        self.busy = True
        self.game.hit()
        self._publish()

        def landed() -> None:
            self._player_count += 1
            self._publish()
            self._continue()
        self._move('player', self.game.table.player[-1], self._player_count, landed)

    def stand(self) -> None:
        if self._closed or self.busy or self.game.table.phase is not Phase.PLAYER:
            return
        self.busy = True
        self.game.stand()
        self._continue()

    def _continue(self) -> None:
        if self.game.table.phase is Phase.PLAYER:
            self.busy = False
            self._publish()
        else:
            self.busy = True
            self._publish()
            self._line('game_bj_reveal', self._reveal)

    def _reveal(self) -> None:
        self.game.reveal_dealer()
        self._dealer_revealed = True
        self._publish(flip=True)
        self._later(550, self._bank)

    def _bank(self) -> None:
        if self.game.table.phase is Phase.DEALER:
            before = len(self.game.table.dealer)
            self.game.dealer_step()
            if len(self.game.table.dealer) > before:
                def landed() -> None:
                    self._dealer_count += 1
                    self._publish()
                    self._later(600, self._bank)
                self._move('dealer', self.game.table.dealer[-1], before, landed)
                return
        if self.game.table.phase is Phase.RESULT:
            self.game.settle()
            self._publish()
            result = self.game.table.result
            assert result is not None
            self._round_event(GameRoundEvent(
                GameId.BLACKJACK, self._session_id, self.game.score.games, result,
                self.game.result_details,
            ))
            self._line('game_bj_' + result, lambda: self._line(
                'game_bj_aside', self._result_emote,
            ))
        else:
            self._later(600, self._bank)

    def _result_emote(self) -> None:
        self._emote('star', 950)

        def restored() -> None:
            text = self._aside
            self._say(text, self.RESULT_PAUSE_MS)
            self._later(self.RESULT_PAUSE_MS, lambda: self._move(
                'gather', None, 0, self._restart,
            ))
        self._later(950, restored)

    def _restart(self) -> None:
        self.game.next_round()
        self._begin()

    def close(self) -> SessionSummary:
        if not self._closed:
            self._closed = True
            self._generation += 1
            if self.pending_timer is not None:
                self._cancel(self.pending_timer)
                self.pending_timer = None
            self._hand(HandView(), False)
            self.game.cancel()
        return self.game.score
