"""Application-owned desktop and pet preferences, independent of storage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


SettingKey = Literal[
    "always_on_top", "auto_walk", "auto_routine", "follow_cursor",
    "spontaneous_talk", "observe_computer", "learn_rhythm",
]


@dataclass
class PetBehaviorSettings:
    """Pet-specific behaviour options, independent of desktop geometry."""

    auto_walk: bool = True
    auto_routine: bool = True
    follow_cursor: bool = True
    spontaneous_talk: bool = True
    observe_computer: bool = True
    learn_rhythm: bool = True


@dataclass
class DesktopDisplaySettings:
    """Window geometry, layering and toolbar placement preferences."""

    x: int | None = None
    y: int | None = None
    scale: int = 1
    always_on_top: bool = True
    toolbar_x: int | None = None
    toolbar_y: int | None = None


@dataclass(init=False)
class PetSettings:
    """Own one mutable settings aggregate with two non-overlapping subobjects.

    Flat constructor properties and version-one JSON keys remain compatible.
    A setting is stored only on its owning subobject, never duplicated here.
    """

    behavior: PetBehaviorSettings
    desktop: DesktopDisplaySettings

    def __init__(
        self, x: int | None = None,
        y: int | None = None,
        scale: int = 1,
        always_on_top: bool = True,
        auto_walk: bool = True,
        auto_routine: bool = True,
        follow_cursor: bool = True,
        spontaneous_talk: bool = True,
        observe_computer: bool = True,
        learn_rhythm: bool = True,
        toolbar_x: int | None = None,
        toolbar_y: int | None = None,
    ) -> None:
        self.desktop = DesktopDisplaySettings(
            x=x,
            y=y,
            scale=scale,
            always_on_top=always_on_top,
            toolbar_x=toolbar_x,
            toolbar_y=toolbar_y,
        )
        self.behavior = PetBehaviorSettings(
            auto_walk=auto_walk,
            auto_routine=auto_routine,
            follow_cursor=follow_cursor,
            spontaneous_talk=spontaneous_talk,
            observe_computer=observe_computer,
            learn_rhythm=learn_rhythm,
        )

    @property
    def x(self) -> int | None:
        return self.desktop.x

    @x.setter
    def x(self, value: int | None) -> None:
        self.desktop.x = value

    @property
    def y(self) -> int | None:
        return self.desktop.y

    @y.setter
    def y(self, value: int | None) -> None:
        self.desktop.y = value

    @property
    def scale(self) -> int:
        return self.desktop.scale

    @scale.setter
    def scale(self, value: int) -> None:
        self.desktop.scale = value

    @property
    def always_on_top(self) -> bool:
        return self.desktop.always_on_top

    @always_on_top.setter
    def always_on_top(self, value: bool) -> None:
        self.desktop.always_on_top = value

    @property
    def auto_walk(self) -> bool:
        return self.behavior.auto_walk

    @auto_walk.setter
    def auto_walk(self, value: bool) -> None:
        self.behavior.auto_walk = value

    @property
    def auto_routine(self) -> bool:
        return self.behavior.auto_routine

    @auto_routine.setter
    def auto_routine(self, value: bool) -> None:
        self.behavior.auto_routine = value

    @property
    def follow_cursor(self) -> bool:
        return self.behavior.follow_cursor

    @follow_cursor.setter
    def follow_cursor(self, value: bool) -> None:
        self.behavior.follow_cursor = value

    @property
    def spontaneous_talk(self) -> bool:
        return self.behavior.spontaneous_talk

    @spontaneous_talk.setter
    def spontaneous_talk(self, value: bool) -> None:
        self.behavior.spontaneous_talk = value

    @property
    def observe_computer(self) -> bool:
        return self.behavior.observe_computer

    @observe_computer.setter
    def observe_computer(self, value: bool) -> None:
        self.behavior.observe_computer = value

    @property
    def learn_rhythm(self) -> bool:
        return self.behavior.learn_rhythm

    @learn_rhythm.setter
    def learn_rhythm(self, value: bool) -> None:
        self.behavior.learn_rhythm = value

    @property
    def toolbar_x(self) -> int | None:
        return self.desktop.toolbar_x

    @toolbar_x.setter
    def toolbar_x(self, value: int | None) -> None:
        self.desktop.toolbar_x = value

    @property
    def toolbar_y(self) -> int | None:
        return self.desktop.toolbar_y

    @toolbar_y.setter
    def toolbar_y(self, value: int | None) -> None:
        self.desktop.toolbar_y = value

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

