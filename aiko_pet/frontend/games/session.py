"""Compose all existing game timelines with web effects and canonical rewards."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from ...application.active_time import SessionInputs
from ...application.game_experience import (
    experience_from_rock_paper_scissors,
    experience_from_session,
)
from ...application.room_contracts import json_value
from ...application.router import ApplicationRouter
from ...games.contracts import GameId, GameRoundEvent
from ...games.mastermind import COLORS
from ...games.playing_cards import Card
from ...games.quiz import QuizSession
from ...games.quiz_catalogue import QuizCatalogue
from ...games.rock_paper_scissors import Move
from ...pet.animation.expression import event_expression
from ...pet.mind import PetMind
from ...pet.routine import context_at
from ...pet.state import PetState
from ..room_communication import COMMUNICATION_ACTIONS
from ..room_playback import RoomPlayback
from ..view_models.mastermind_models import CodeView
from .blackjack_sequence import BlackjackSequence
from .connect_four_sequence import ConnectFourSequence
from .deferred_executor import DeferredSearchExecutor
from .mastermind_sequence import MastermindSequence
from .quiz_sequence import QuizSequence
from .rock_paper_scissors_sequence import RockPaperScissorsSequence
from .room_effects import RoomGameEffects
from .tic_tac_toe_sequence import TicTacToeSequence


class GameSessionCoordinator:
    """One transient game; the existing coordinator alone grants pet effects."""

    def __init__(
        self,
        router: ApplicationRouter,
        state: PetState,
        mind: PetMind,
        playback: RoomPlayback,
        inputs: Callable[[], SessionInputs],
    ) -> None:
        self.router, self.state, self.mind = router, state, mind
        self.playback, self.inputs = playback, inputs
        self.sequence: Any = None
        self.game_id: GameId | None = None
        self.visible: dict[str, Any] = {}
        self._busy = False
        self.effects: RoomGameEffects | None = None

    def _dialogue(self, event: str) -> str:
        reaction = self.mind.select_reaction(
            event, self.state, context_at(time.time()), time.monotonic()
        )
        return reaction.text if reaction is not None else ""

    def _round(self, event: GameRoundEvent) -> None:
        self.router.observe_game_round(event, inputs=self.inputs())

    def _present(self, **data: Any) -> None:
        self.visible.update({key: json_value(value) for key, value in data.items()})

    def _animate(self, name: str) -> None:
        """Speech owns V3 expressions; other gestures have a bounded lifetime."""
        if name == "idle" or name in COMMUNICATION_ACTIONS:
            self.playback.stop_animation()
            self.playback.express(None)
        else:
            self.playback.start_action(name, 1.0)

    def open(self, game_id: str) -> None:
        self.close()
        self.game_id = GameId(game_id)
        self.effects = RoomGameEffects(self.playback)
        common: dict[str, Any] = dict(
            schedule=self.playback.schedule,
            cancel=self.playback.cancel_timer,
            say=self.playback.comment,
            animate=self._animate,
            dialogue=self._dialogue,
            round_event=self._round,
            express_event=lambda event: self.playback.express(event_expression(event)),
        )
        emote = self.playback.emote
        if self.game_id == GameId.ROCK_PAPER_SCISSORS:
            self.sequence = RockPaperScissorsSequence(
                **common,
                show_emote=emote,
                show_aiko_hand=lambda move, _ms: self._present(aiko=move),
                reveal_player=lambda move, score: self._present(
                    player=move, score=score
                ),
                set_busy=self._set_busy,
                clear_hand=lambda: self._present(aiko=None, player=None),
                presentation=self.effects.presentation,
            )
        elif self.game_id == GameId.TIC_TAC_TOE:
            self.sequence = TicTacToeSequence(
                **common,
                emote=emote,
                present=lambda board, score: self._present(board=board, score=score),
            )
        elif self.game_id == GameId.BLACKJACK:
            self.sequence = BlackjackSequence(
                **common,
                emote=emote,
                present=lambda table, score: self._present(table=table, score=score),
                hand=lambda hand, flip: self._present(hand=hand, flip=flip),
                motion=self._card_motion,
                silence=self.playback.silence,
            )
        elif self.game_id == GameId.CONNECT_FOUR:
            self.sequence = ConnectFourSequence(
                **common,
                emote=emote,
                executor=DeferredSearchExecutor(self.playback.schedule),
                present=lambda board, score, busy, drop: self._present(
                    board=board,
                    score=score,
                    busy=busy,
                    drop=drop,
                ),
                throw=self.effects.throw,
            )
        elif self.game_id == GameId.MASTERMIND:
            self.visible["colors"] = list(COLORS)
            self.sequence = MastermindSequence(
                **common,
                emote=emote,
                present=lambda view, score, busy, count: self._present(
                    view=view,
                    score=score,
                    busy=busy,
                    feedback_count=count,
                ),
                show_code=self._show_code,
                hide_code=lambda: self._present(code=None),
                finale=self.effects.finale,
            )
        else:
            self.sequence = QuizSequence(
                QuizSession(QuizCatalogue.load(), self.mind.rng),
                **common,
                emote=emote,
                present=lambda: None,
            )
        self.sequence.greet()

    def _show_code(self, code: CodeView) -> None:
        if self.effects is not None and all(slot is None for slot in code.slots):
            self.effects.safe_frame = 0
            self.effects.snack = False
        self._present(code=code)

    def _card_motion(
        self, kind: str, card: Card | None, index: int, done: Callable[[], None]
    ) -> None:
        assert self.effects is not None
        # Never send a hole-card face to the renderer during its dealing flight.
        visible = kind != "dealer" or index == 0 or self.sequence.dealer_revealed
        self.effects.card(kind, card if visible else None, index, done)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy

    def action(self, action: str, value: Any = None) -> None:
        if self.sequence is None or self.game_id is None:
            raise ValueError("Kein Spiel geöffnet.")
        flow = self.sequence
        allowed = {
            GameId.ROCK_PAPER_SCISSORS: {"choose"},
            GameId.TIC_TAC_TOE: {"choose", "next"},
            GameId.BLACKJACK: {"hit", "stand", "next"},
            GameId.CONNECT_FOUR: {"choose", "next"},
            GameId.MASTERMIND: {"submit", "next"},
            GameId.QUIZ: {"answer", "next"},
        }
        if action not in allowed[self.game_id]:
            raise ValueError("Diese Aktion gehört nicht zum aktuellen Spiel.")
        if self.game_id == GameId.ROCK_PAPER_SCISSORS and action == "choose":
            flow.choose(Move(value))
        elif self.game_id == GameId.TIC_TAC_TOE:
            flow.choose(int(value)) if action == "choose" else flow.next_round()
        elif self.game_id == GameId.BLACKJACK:
            if action == "hit":
                flow.hit()
            elif action == "stand":
                flow.stand()
            elif action == "next":
                flow.advance()
            else:
                raise ValueError("Unbekannte Kartenaktion.")
        elif self.game_id == GameId.CONNECT_FOUR:
            flow.choose(int(value)) if action == "choose" else flow.next_round()
        elif self.game_id == GameId.MASTERMIND:
            flow.submit(tuple(value)) if action == "submit" else flow.next_round()
        elif self.game_id == GameId.QUIZ:
            flow.answer(str(value)) if action == "answer" else flow.advance()
        else:
            raise ValueError("Unbekannte Spielaktion.")

    def snapshot(self) -> dict[str, Any] | None:
        if self.sequence is None or self.game_id is None:
            return None
        data = {"id": self.game_id.value, **self.visible}
        data["props"] = self.effects.snapshot() if self.effects else {}
        flow = self.sequence
        data["busy"] = getattr(flow, "busy", self._busy)
        if self.game_id == GameId.QUIZ:
            game = flow.game
            question = game.current
            data.update(
                question=question.text if flow.question_visible else "",
                answers=json_value(question.answers[: flow.visible_answers]),
                correct=question.correct_answer_id if flow.revealed else None,
                explanation=question.explanation if flow.revealed else "",
                selected=game.selected,
                finished=game.finished,
                index=game.index,
                score=flow.visible_correct,
                revealed=flow.revealed,
            )
        elif self.game_id == GameId.ROCK_PAPER_SCISSORS:
            data["score"] = json_value(flow.score)
        return data

    def close(self) -> None:
        if self.sequence is None:
            return
        flow, game_id = self.sequence, self.game_id
        self.sequence = None
        summary = flow.close()
        if self.effects is not None:
            self.effects.close()
            self.effects = None
        if game_id == GameId.ROCK_PAPER_SCISSORS:
            self.router.complete_game(
                experience_from_rock_paper_scissors(flow.score), inputs=self.inputs()
            )
        elif game_id != GameId.QUIZ:
            self.router.complete_game(
                experience_from_session(summary), inputs=self.inputs()
            )
        self.game_id = None
        self.visible.clear()
        self._busy = False
        self.playback.stop_animation()
        self.playback.express(None)
