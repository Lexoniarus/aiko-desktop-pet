"""Present phase feedback through the existing reaction player and bubble."""

from collections.abc import Callable

from ...application.object_feedback import FeedbackReceipt, ObjectFeedback
from ...pet.animation.item_assets import ItemCatalog
from ...pet.mind.catalog import Reaction
from ..view_models.object_reactions import format_object_reaction
from .reaction_player import ReactionPlayer


class ObjectFeedbackPresenter:
    def __init__(self, player: ReactionPlayer, items: ItemCatalog) -> None:
        self._player, self._items = player, items

    def show(
        self, cue: ObjectFeedback, reaction: Reaction,
        completed: Callable[[FeedbackReceipt], None],
    ) -> None:
        self._player.play(
            format_object_reaction(reaction, cue.identity, self._items),
            2300, animate=False,
            on_complete=lambda success: completed(FeedbackReceipt(cue.key, success)),
        )
