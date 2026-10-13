"""Status-window operations, separated from application read contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..presentation.contracts import StatusSnapshot as StatusSnapshot


@dataclass(frozen=True, slots=True)
class StatusActions:
    interact: Callable[[str], None]
    quit: Callable[[], None]
    closed: Callable[[], None]
