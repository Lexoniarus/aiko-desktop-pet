"""Immutable contracts for independently rendered hand-held items."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ItemSprite:
    """A scale-specific PNG and its pivot in image pixels."""

    path: Path
    pivot: tuple[float, float]
    display_path: Path | None = None
    zoom: int = 1

    @property
    def render_path(self) -> Path:
        return self.display_path or self.path


@dataclass(frozen=True, slots=True)
class HandItem:
    """One asset shared by picker/overlays, with native 1x and 2x sprites."""

    key: str
    label: str
    icon: Path | None
    sprites: Mapping[int, ItemSprite]


@dataclass(frozen=True, slots=True)
class ItemCatalog:
    foods: Mapping[str, HandItem]
    weapons: Mapping[str, HandItem]
    readables: Mapping[str, ReadableItem] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReadableItem:
    key: str
    label: str
    icon: Path
    states: Mapping[str, Mapping[int, ItemSprite]]
    hand_offset: tuple[float, float] = (0.0, 0.0)
    world_zoom: int = 1
    state_offsets: Mapping[str, tuple[float, float]] = field(default_factory=dict)

    @property
    def sprites(self) -> Mapping[int, ItemSprite]:
        return self.states["closed_world"]
