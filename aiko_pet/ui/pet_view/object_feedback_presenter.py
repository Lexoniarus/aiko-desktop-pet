"""Present phase feedback through the existing reaction player and bubble."""

from collections.abc import Callable

from ...application.object_feedback import FeedbackReceipt, ObjectFeedback
from ...pet.animation.item_assets import ItemCatalog
from ...pet.mind.catalog import Reaction
from ..view_models.object_reactions import format_object_reaction
from .reaction_player import ReactionPlayer


class ObjectFeedbackPresenter:
    OFFER_EVENTS = ("object_offer", "object_refuse")

    def __init__(self, player: ReactionPlayer, items: ItemCatalog) -> None:
        self._player, self._items = player, items

    def cancel_offer(self) -> None:
        """Ending a cursor gesture must not cancel unrelated character speech."""
        if self._player.event in self.OFFER_EVENTS:
            self._player.cancel()

    @property
    def non_offer_playback_active(self) -> bool:
        """An offer's own preview does not exclude its authorized handover."""
        return self._player.active and self._player.event not in self.OFFER_EVENTS

    def show(
        self, cue: ObjectFeedback, reaction: Reaction,
        completed: Callable[[FeedbackReceipt], None],
    ) -> None:
        self._player.play(
            format_object_reaction(reaction, cue.identity, self._items),
            animate=False,
            subject=cue.record_id,
            on_complete=lambda success: completed(FeedbackReceipt(cue.key, success)),
        )
