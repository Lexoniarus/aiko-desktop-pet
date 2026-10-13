"""Legacy re-exports of presentation contracts.

New application services should use semantic snapshots from read_snapshot,
not UI labels or desktop geometry. Existing imports remain type-identical.
"""

from __future__ import annotations

from ..presentation.contracts import (
    HoverAnchor as HoverAnchor,
    HoverSnapshot as HoverSnapshot,
    SettingsSnapshot as SettingsSnapshot,
    StatusSnapshot as StatusSnapshot,
)
