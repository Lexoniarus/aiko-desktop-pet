"""Immutable hardware readings and deterministic effort classification."""

from __future__ import annotations

from ...telemetry import (
    ComputerSnapshot as ComputerSnapshot,
    workload_intensity as workload_intensity,
)



def workload_description(snapshot: ComputerSnapshot) -> str:
    """Readable private effort, not a recitation of component names."""
    effort = workload_intensity(snapshot)
    if snapshot.measured_at <= 0 or effort is None:
        return "Ich orientiere mich noch ..."
    if effort >= 0.9:
        return "Ich bin gerade voll konzentriert."
    if effort >= 0.7:
        return "Ich habe ordentlich zu tun."
    if effort >= 0.36:
        return "Ich bin beschäftigt."
    return "Ich habe gerade etwas Ruhe."


def percent_label(number: float | None) -> str:
    return "–" if number is None else f"{max(0, min(100, round(number)))} %"
