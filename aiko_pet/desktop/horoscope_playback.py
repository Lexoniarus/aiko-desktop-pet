"""Present a persisted daily episode through the existing reaction player."""

from dataclasses import replace
from typing import Callable

from ..application.social_content import PreparedSocialContent
from ..application.social_coordinator import SocialContentCoordinator
from ..ui.pet_view.reaction_player import ReactionPlayer
from ..ui.pet_view.speech_presenter import SpeechPresenter


class HoroscopePlayback:
    def __init__(
        self,
        content: SocialContentCoordinator,
        player: ReactionPlayer,
        speech: SpeechPresenter,
        care: Callable[[PreparedSocialContent], None],
    ) -> None:
        self._content, self._player, self._speech, self._care = (
            content,
            player,
            speech,
            care,
        )
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    def stop(self) -> None:
        if self._active:
            self._player.cancel()

    def start(self, item: PreparedSocialContent) -> bool:
        if not self._content.admit_horoscope(item, lambda: self._care(item)):
            return False
        day = self._content.horoscope
        text = day.reading
        assert text is not None
        beats = item.reaction.beats
        offset = day.index
        # Reintroduce the role without replaying completed provider bubbles.
        prefix = (beats[0],) if offset else ()
        reaction = replace(item.reaction, beats=(*prefix, *beats[offset:]))

        def progress(index: int) -> bool:
            current = offset + max(0, index - len(prefix))
            return self._content.horoscope_progress(
                text.date,
                current,
                completed=current == len(beats),
            )

        def finished(_complete: bool) -> None:
            self._active = False
            self._speech.attribution = ""

        self._player.cancel()
        self._speech.attribution = text.footer
        self._active = True
        self._player.play(reaction, on_progress=progress, on_complete=finished)
        return True
