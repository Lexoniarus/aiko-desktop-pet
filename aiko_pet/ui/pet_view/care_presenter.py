"""Render the visual result of an already-executed pet care command.

The application owns nutrition, friendship and care dialogue decisions.
Only this presenter maps a CareOutcome to the existing desktop visuals.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

from ...application.controller import CareOutcome
from ...pet.mind.catalog import Reaction
from ..view_models.care_text import format_care_response


@dataclass(frozen=True, slots=True)
class CareViewPorts:
    """Explicit visual capabilities without a reference to DesktopPet."""

    set_item: Callable[[str], None]
    cancel_action: Callable[[float], None]
    start_action: Callable[[str, float], None]
    cancel_followup: Callable[[], None]
    react: Callable[[Reaction, int], None]
    show_text: Callable[[str, int], None]
    refresh_toolbar: Callable[[], None]
    refresh_status: Callable[[], None]


class CarePresenter:
    """Display accepted care without repeating domain transitions."""

    def __init__(self, ports: CareViewPorts) -> None:
        self._ports = ports

    def present(
        self, outcome: CareOutcome, *,
        now: float, sleeping: bool,
    ) -> None:
        ports = self._ports
        action = outcome.result.action
        if outcome.consumed_item_id is not None:
            ports.set_item(outcome.consumed_item_id)
        if action == "sleep":
            ports.cancel_action(now)
        visual = {
            "feed": "eat",
            "energy_drink": "eat",
            "pet": "petting",
        }.get(action)
        if visual == "eat" and outcome.consumed_item_id is None:
            visual = None
        reaction = outcome.reaction
        if visual is not None and not sleeping:
            if reaction is not None:
                reaction = replace(reaction, animation=visual)
            else:
                ports.start_action(visual, 0.0)
        if reaction is None:
            ports.cancel_followup()
            ports.show_text(format_care_response(outcome.result), 2450)
        else:
            ports.react(reaction, 2900)
        ports.refresh_toolbar()
        ports.refresh_status()
