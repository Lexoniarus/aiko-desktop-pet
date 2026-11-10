"""Route historical speech gestures to the existing V3 expression channel."""

from dataclasses import replace

from ..pet.animation.expression import Expression
from ..pet.mind.catalog import Reaction

COMMUNICATION_ACTIONS = {
    "waiting": Expression.NEUTRAL,
    "waving": Expression.NEUTRAL,
    "waving-greeting": Expression.POSITIVE,
    "jumping": Expression.POSITIVE,
    "failed": Expression.DOWNCAST,
    "review": Expression.QUESTIONING,
}


def communication_reaction(reaction: Reaction | None) -> Reaction | None:
    """Keep authored/state-aware intent; only missing intent uses a fallback.

    Physical care/object actions are deliberately outside this mapping. A V3
    expression must not replace their hand markers or object ownership.
    """
    if reaction is None or reaction.animation not in COMMUNICATION_ACTIONS:
        return reaction
    return replace(
        reaction,
        animation="idle",
        expression=reaction.expression or COMMUNICATION_ACTIONS[reaction.animation],
    )
