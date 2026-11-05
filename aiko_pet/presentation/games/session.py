"""Compose all existing game timelines with web effects and canonical rewards."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from ...games.contracts import GameId, GameRoundEvent
from ...games.quiz import QuizSession
from ...games.quiz_catalogue import QuizCatalogue
from ...games.rock_paper_scissors import Move
from ...games.mastermind import COLORS
from ...pet.mind import PetMind
from ...pet.routine import context_at
from ...pet.state import PetState
from .blackjack_sequence import BlackjackSequence
from .connect_four_sequence import ConnectFourSequence
from .deferred_executor import DeferredSearchExecutor
from .mastermind_sequence import MastermindSequence
from .quiz_sequence import QuizSequence
from .rock_paper_scissors_sequence import RockPaperScissorsSequence
from .tic_tac_toe_sequence import TicTacToeSequence
from ..room_playback import RoomPlayback
from ...application.active_time import SessionInputs
from ...application.game_experience import experience_from_rock_paper_scissors, experience_from_session
from ...application.room_contracts import json_value
from ...application.router import ApplicationRouter


class GameSessionCoordinator:
    """One transient game; the existing coordinator alone grants pet effects."""

    def __init__(
        self, router: ApplicationRouter, state: PetState, mind: PetMind,
        playback: RoomPlayback, inputs: Callable[[], SessionInputs],
    ) -> None:
        self.router, self.state, self.mind = router, state, mind
        self.playback, self.inputs = playback, inputs
        self.sequence: Any = None
        self.game_id: GameId | None = None
        self.visible: dict[str, Any] = {}
        self._busy = False

    def _dialogue(self, event: str) -> str:
        reaction = self.mind.select_reaction(event, self.state,
                                             context_at(time.time()), time.monotonic())
        return reaction.text if reaction is not None else ""

    def _round(self, event: GameRoundEvent) -> None:
        self.router.observe_game_round(event, inputs=self.inputs())

    def _present(self, **data: Any) -> None:
        self.visible.update({key: json_value(value) for key, value in data.items()})

    def open(self, game_id: str) -> None:
        self.close()
        self.game_id = GameId(game_id)
        common: dict[str, Any] = dict(
            schedule=self.playback.schedule, cancel=self.playback.cancel_timer,
            say=self.playback.comment,
            animate=lambda name: self.playback.play_animation(name)
            if name != "idle" else self.playback.stop_animation(),
            dialogue=self._dialogue, round_event=self._round,
        )
        emote = self.playback.emote
        if self.game_id == GameId.ROCK_PAPER_SCISSORS:
            self.sequence = RockPaperScissorsSequence(
                **common, show_emote=emote,
                show_aiko_hand=lambda move, _ms: self._present(aiko=move),
                reveal_player=lambda move, score: self._present(player=move, score=score),
                set_busy=self._set_busy,
                clear_hand=lambda: self._present(aiko=None, player=None),
            )
        elif self.game_id == GameId.TIC_TAC_TOE:
            self.sequence = TicTacToeSequence(
                **common, emote=emote,
                present=lambda board, score: self._present(board=board, score=score),
            )
        elif self.game_id == GameId.BLACKJACK:
            self.sequence = BlackjackSequence(
                **common, emote=emote,
                present=lambda table, score: self._present(table=table, score=score),
                hand=lambda hand, flip: self._present(hand=hand, flip=flip),
            )
        elif self.game_id == GameId.CONNECT_FOUR:
            self.sequence = ConnectFourSequence(
                **common, emote=emote, executor=DeferredSearchExecutor(self.playback.schedule),
                present=lambda board, score, busy, drop: self._present(
                    board=board, score=score, busy=busy, drop=drop,
                ),
            )
        elif self.game_id == GameId.MASTERMIND:
            self.visible["colors"] = list(COLORS)
            self.sequence = MastermindSequence(
                **common, emote=emote,
                present=lambda view, score, busy, count: self._present(
                    view=view, score=score, busy=busy, feedback_count=count,
                ),
                show_code=lambda code: self._present(code=code),
                hide_code=lambda: self._present(code=None),
            )
        else:
            self.sequence = QuizSequence(
                QuizSession(QuizCatalogue.load(), self.mind.rng),
                **common, emote=emote, present=lambda: None,
            )
        self.sequence.greet()

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
        flow = self.sequence
        data["busy"] = getattr(flow, "busy", self._busy)
        if self.game_id == GameId.QUIZ:
            game = flow.game
            question = game.current
            data.update(
                question=question.text if flow.question_visible else "",
                answers=json_value(question.answers[:flow.visible_answers]),
                correct=question.correct_answer_id if flow.revealed else None,
                explanation=question.explanation if flow.revealed else "",
                selected=game.selected, finished=game.finished,
                index=game.index, score=flow.visible_correct, revealed=flow.revealed,
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
        if game_id == GameId.ROCK_PAPER_SCISSORS:
            self.router.complete_game(experience_from_rock_paper_scissors(flow.score),
                                      inputs=self.inputs())
        elif game_id != GameId.QUIZ:
            self.router.complete_game(experience_from_session(summary), inputs=self.inputs())
        self.game_id = None
        self.visible.clear()
        self._busy = False
        self.playback.stop_animation()
