"""Pure active-time decisions for withholding one committed object."""

from dataclasses import dataclass, replace

from ..balance import BALANCE
from ..moodlet_catalog import MOODLET_CATALOG
from ..moodlets import MoodletId, WithholdingParameters
from .object_events import ObjectEvent


@dataclass(frozen=True, slots=True)
class WithholdingEpisode:
    takes: int = 0
    held_since: float | None = None
    requested_at: float = float("-inf")
    escalated_at: float = float("-inf")
    charged_loss: float = 0.0
    moodlet_trigger_at: float | None = None

    def taken(self, now: float) -> "WithholdingEpisode":
        return replace(self, takes=self.takes + 1, held_since=now, requested_at=now,
                       moodlet_trigger_at=None)

    def returned(self) -> "WithholdingEpisode":
        return replace(self, held_since=None)


@dataclass(frozen=True, slots=True)
class WithholdingResponse:
    episode: WithholdingEpisode
    event: ObjectEvent
    irritated: bool
    friendship_loss: float
    reinforces_moodlet: bool = False


def choose_withholding_response(
    episode: WithholdingEpisode, now: float,
) -> WithholdingResponse | None:
    if (episode.held_since is None or now < episode.held_since
            or now - episode.requested_at < BALANCE.number(
                "object_withholding", "request_interval_seconds",
            )):
        return None
    irritated = (
        episode.takes >= BALANCE.integer("object_withholding", "repeated_takes")
        or now - episode.held_since >= BALANCE.number(
            "object_withholding", "grace_seconds",
        )
    )
    loss = 0.0
    if irritated and now - episode.escalated_at >= BALANCE.number(
        "object_withholding", "loss_interval_seconds",
    ):
        loss = BALANCE.number("object_withholding", "friendship_loss")
    parameters = MOODLET_CATALOG.definitions[MoodletId.WITHHELD].parameters
    assert isinstance(parameters, WithholdingParameters)
    trigger = irritated and (episode.moodlet_trigger_at is None
                            or now - episode.moodlet_trigger_at
                            >= parameters.escalation_seconds)
    return WithholdingResponse(
        replace(episode, requested_at=now,
                escalated_at=now if loss else episode.escalated_at,
                charged_loss=episode.charged_loss + loss,
                moodlet_trigger_at=now if trigger else episode.moodlet_trigger_at),
        "object_withheld" if irritated else "object_request_return",
        irritated, loss, trigger,
    )
