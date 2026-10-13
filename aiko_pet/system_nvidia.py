"""Optional NVIDIA executable discovery and multi-GPU CSV parsing."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def nvidia_executable() -> str | None:
    found = shutil.which("nvidia-smi")
    if found:
        return found
    if sys.platform == "win32":
        for base in (
            os.environ.get("WINDIR", r"C:\Windows"),
            os.environ.get("ProgramFiles", r"C:\Program Files"),
        ):
            parent = Path(base)
            for subpath in (
                "System32/nvidia-smi.exe",
                "NVIDIA Corporation/NVSMI/nvidia-smi.exe",
            ):
                candidate = parent / subpath
                if candidate.is_file():
                    return str(candidate)
    return None


def parse_nvidia_reading(output: str) -> tuple[float | None, float | None]:
    """Select highest utilization on multi-GPU machines; no silent fake zeros."""
    readings: list[tuple[float, float | None]] = []
    for line in output.splitlines():
        fields = [item.strip() for item in line.split(",")]
        if len(fields) < 3:
            continue
        try:
            utilization = float(fields[0])
            used = float(fields[1])
            total = float(fields[2])
        except ValueError:
            continue
        if not 0 <= utilization <= 100 or used < 0 or total < 0:
            continue
        memory = min(100, 100 * used / total) if total > 0 else None
        readings.append((utilization, memory))
    if not readings:
        return None, None
    return max(readings, key=lambda item: item[0])
