"""Immutable hardware readings and deterministic effort classification."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComputerSnapshot:
    cpu: float | None = None
    gpu: float | None = None
    ram: float | None = None
    gpu_memory: float | None = None
    uptime_hours: float | None = None
    measured_at: float = 0.0

    def is_busy(self) -> bool:
        return (workload_intensity(self) or 0.0) >= 0.70


def workload_intensity(snapshot: ComputerSnapshot) -> float | None:
    """Estimate *effort*, not task identity or memory allocation alone.

    CPU/GPU utilization carry the main signal; high RAM/VRAM occupancy adds
    moderate pressure. Unknown sensors never turn into fabricated 0% loads.
    """
    if all(value is None for value in (snapshot.cpu, snapshot.gpu, snapshot.ram)):
        return None
    cpu = max(0.0, min(1.0, (snapshot.cpu or 0) / 100))
    gpu = max(0.0, min(1.0, (snapshot.gpu or 0) / 100))
    work = max(cpu, gpu) + 0.08 * min(cpu, gpu)
    if snapshot.ram is not None and snapshot.ram > 82:
        work += 0.12 * min(1.0, (snapshot.ram - 82) / 18)
    if snapshot.gpu_memory is not None and snapshot.gpu_memory > 94:
        work += 0.035 * min(1.0, (snapshot.gpu_memory - 94) / 6)
    return round(min(1.0, work), 3)


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
