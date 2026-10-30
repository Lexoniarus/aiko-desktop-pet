"""Sparse autonomous presentation, always interrupted by player decisions."""
from collections.abc import Callable

from .game_presentation import GamePresentation


class GameWaiting:
    def __init__(
        self, schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None], presentation: GamePresentation | None,
        point: Callable[[], tuple[float, float]], comment: Callable[[], None],
    ) -> None:
        self._schedule, self._cancel = schedule, cancel
        self._presentation, self._point, self._comment = presentation, point, comment
        self._timer: str | None = None
        self._generation = self._step = 0
        self.active = False

    def set_active(self, active: bool) -> None:
        if active == self.active:
            return
        self.active = active
        self._generation += 1
        if self._timer is not None:
            self._cancel(self._timer)
            self._timer = None
        if self._presentation is not None:
            self._presentation.cancel()
            self._presentation.look(None)
        if active:
            self._step = 0
            self._later()

    def _later(self) -> None:
        generation = self._generation

        def run() -> None:
            if (not self.active or generation != self._generation
                    or self._timer != token):
                return
            self._timer = None
            presentation = self._presentation
            if presentation is not None:
                if self._step % 3 == 0:
                    presentation.look(self._point())
                elif self._step % 3 == 1:
                    presentation.look(None)
                    presentation.action('idle-question-request', 2600,
                                        lambda _: None, lambda: None)
                else:
                    presentation.look(None)
                    self._comment()
            self._step += 1
            self._later()
        token = self._schedule(11000, run)
        self._timer = token
