"""Application-owned desktop and pet preferences, independent of storage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PetSettings:
    x: int | None = None
    y: int | None = None
    scale: int = 1
    always_on_top: bool = True
    auto_walk: bool = True
    auto_routine: bool = True
    follow_cursor: bool = True
    spontaneous_talk: bool = True
    observe_computer: bool = True
    learn_rhythm: bool = True
    toolbar_x: int | None = None
    toolbar_y: int | None = None

    @classmethod
    def from_dict(cls, payload: Any) -> PetSettings:
        if not isinstance(payload, dict):
            return cls()

        def coordinate(value: Any) -> int | None:
            if type(value) is not int:  # bool isn't a coordinate
                return None
            return value if -20_000 <= value <= 20_000 else None

        return cls(
            x=coordinate(payload.get("x")),
            y=coordinate(payload.get("y")),
            scale=2 if payload.get("scale") == 2 else 1,
            always_on_top=payload.get("always_on_top") is not False,
            auto_walk=payload.get("auto_walk") is not False,
            auto_routine=payload.get("auto_routine") is not False,
            follow_cursor=payload.get("follow_cursor") is not False,
            spontaneous_talk=payload.get("spontaneous_talk") is not False,
            observe_computer=payload.get("observe_computer") is not False,
            learn_rhythm=payload.get("learn_rhythm") is not False,
            toolbar_x=coordinate(payload.get("toolbar_x")),
            toolbar_y=coordinate(payload.get("toolbar_y")),
        )

    def to_dict(self) -> dict[str, int | bool | None]:
        return {
            "x": self.x,
            "y": self.y,
            "scale": self.scale,
            "always_on_top": self.always_on_top,
            "auto_walk": self.auto_walk,
            "auto_routine": self.auto_routine,
            "follow_cursor": self.follow_cursor,
            "spontaneous_talk": self.spontaneous_talk,
            "observe_computer": self.observe_computer,
            "learn_rhythm": self.learn_rhythm,
            "toolbar_x": self.toolbar_x,
            "toolbar_y": self.toolbar_y,
        }

