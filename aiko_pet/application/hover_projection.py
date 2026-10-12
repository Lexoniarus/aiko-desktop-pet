"""Project pet and local telemetry into an immutable hover read model."""

from __future__ import annotations

from ..domain import PetState
from ..routine import TimeContext
from ..system_activity import (
    ComputerSnapshot,
    percent_label,
    workload_description,
)
from ..ui.hover_contracts import HoverSnapshot


def project_hover(
    state: PetState,
    context: TimeContext,
    computer: ComputerSnapshot,
    *,
    observe_computer: bool,
) -> HoverSnapshot:
    """Snapshot values before presenting; this never mutates game state."""
    if observe_computer:
        hardware = (
            f"MEIN RECHNER   CPU {percent_label(computer.cpu)}"
            f"   ·   GPU {percent_label(computer.gpu)}"
            f"   ·   RAM {percent_label(computer.ram)}"
        )
        workload = workload_description(computer)
    else:
        hardware = "Rechnerbeobachtung deaktiviert"
        workload = ""
    return HoverSnapshot(
        header=f"{context.label}   ↔ Ziehen",
        sleep_label="Wecken" if state.sleeping else "Schlafen",
        feed_label=state.feed_label(context),
        needs=(
            ("satiety", state.satiety), ("mood", state.mood),
            ("energy", state.energy), ("social", state.social),
            ("affection", state.affection), ("friendship", state.friendship),
        ),
        friendship_level=state.friendship_level,
        hardware_line=hardware,
        workload_line=workload,
    )
