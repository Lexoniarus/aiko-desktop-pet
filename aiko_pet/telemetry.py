"""Hardware-independent immutable workload evidence and effort calculation.

Application policies and platform-specific samplers depend on this shared
value contract, which never calls an operating-system API.
"""

from __future__ import annotations

import math
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


def consumption_load(snapshot: ComputerSnapshot) -> float | None:
    """Physical CPU/GPU use for needs; allocated RAM/VRAM is not computation."""
    values = [
        max(0.0, min(1.0, value / 100.0))
        for value in (snapshot.cpu, snapshot.gpu)
        if value is not None and math.isfinite(value)
    ]
    return max(values) if values else None


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
