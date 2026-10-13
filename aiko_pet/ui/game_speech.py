"""Small adapter giving minigames Aiko's existing character speech bubble."""

from __future__ import annotations

from collections.abc import Callable

from ..presentation.reaction_playback import ReactionPlayer
from .speech_presenter import SpeechPresenter


class GameSpeech:
    """Exclusive, cancellable speech channel while a minigame is open."""

    def __init__(
        self, reactions: ReactionPlayer, speech: SpeechPresenter,
        mark_spoken: Callable[[], None],
    ) -> None:
        self._reactions = reactions
        self._speech = speech
        self._mark_spoken = mark_spoken

    def start(self) -> None:
        self._reactions.cancel()
        self._speech.hide()

    def say(self, phrase: str, duration_ms: int) -> None:
        """Reuse the character bubble, never a secondary game text label."""
        self._mark_spoken()
        self._speech.show_text(phrase, duration_ms)

    def stop(self) -> None:
        self._speech.hide()
