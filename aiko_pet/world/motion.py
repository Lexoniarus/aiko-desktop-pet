"""Analytic item motion in World units; positive vertical velocity points up."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class ItemMotion:
    vx: float = 0.0
    vy: float = 0.0
    contacts: int = 0
    age: float = 0.0
    settling: bool = False

    def __post_init__(self) -> None:
        if (not all(math.isfinite(v) for v in (self.vx, self.vy, self.age))
                or self.age < 0 or type(self.contacts) is not int or self.contacts < 0
                or type(self.settling) is not bool):
            raise ValueError("Invalid item motion")


@dataclass(frozen=True, slots=True)
class MotionParameters:
    gravity: float
    restitution: float
    horizontal_damping: float
    inward_factor: float
    minimum_bounce_speed: float
    settling_speed: float
    maximum_contacts: int
    maximum_seconds: float

    def __post_init__(self) -> None:
        positive = (self.gravity, self.inward_factor, self.minimum_bounce_speed,
                    self.settling_speed, self.maximum_seconds)
        if (not all(math.isfinite(v) and v > 0 for v in positive)
                or not 0 < self.restitution < 1
                or not 0 < self.horizontal_damping < 1
                or type(self.maximum_contacts) is not int
                or not 1 <= self.maximum_contacts <= 32):
            raise ValueError("Invalid motion parameters")


@dataclass(frozen=True, slots=True)
class MotionStep:
    x: float
    height: float
    motion: ItemMotion | None
    contacted: bool


def _horizontal(x: float, velocity: float, elapsed: float,
                left: float, right: float) -> float:
    # An outside object approaches the nearest safe edge; once inside it stays.
    return max(min(left, x), min(x + velocity * elapsed, max(right, x)))


def advance_motion(x: float, height: float, motion: ItemMotion, elapsed: float,
                   bounds: tuple[float, float], parameters: MotionParameters
                   ) -> MotionStep:
    """Consume elapsed time at exact contacts, then finish a short ground slide.

    The inward impulse is an authored placement rule. Restitution and damping
    reduce impact energy; thresholds and budgets eliminate infinite bounce tails.
    No portion becomes resting between contacts.
    """
    left, right = bounds
    if (not all(math.isfinite(v) for v in (x, height, elapsed, left, right))
            or x < 0 or height < 0 or elapsed < 0 or left < 0 or right < left):
        raise ValueError("Invalid motion geometry/time")
    remaining, contacted = elapsed, False
    current = motion
    while remaining > 0:
        target = max(left, min(x, right))
        if current.settling:
            distance = target - x
            travel = parameters.settling_speed * remaining
            if abs(distance) <= travel:
                return MotionStep(target, 0, None, contacted)
            x += math.copysign(travel, distance)
            current = replace(current, age=current.age + remaining)
            return MotionStep(x, 0, current, contacted)
        contact = contact_time(height, current.vy, parameters.gravity)
        step = min(remaining, contact)
        x = _horizontal(x, current.vx, step, left, right)
        height, vy = flight(height, current.vy, step, parameters.gravity)
        current = replace(current, vy=vy, age=current.age + step)
        remaining = max(0.0, remaining - step)
        if step < contact:
            break
        contacted = True
        height = 0.0
        count = current.contacts + 1
        launch = abs(vy) * parameters.restitution
        target = max(left, min(x, right))
        if (launch < parameters.minimum_bounce_speed
                or count >= parameters.maximum_contacts
                or current.age >= parameters.maximum_seconds):
            if target == x:
                return MotionStep(x, 0, None, True)
            current = ItemMotion(contacts=count, age=current.age, settling=True)
        else:
            vx = current.vx * parameters.horizontal_damping
            if count == 1 and target != x:
                vx = math.copysign(abs(vy) * parameters.inward_factor, target - x)
            current = ItemMotion(vx, launch, count, current.age)
    return MotionStep(x, height, current, contacted)


def contact_time(height: float, velocity: float, gravity: float) -> float:
    """Next descending contact, including an upward launch from ground level."""
    if (not all(math.isfinite(v) for v in (height, velocity, gravity))
            or height < 0 or gravity <= 0):
        raise ValueError("Invalid ballistic values")
    root = math.sqrt(velocity * velocity + 2 * gravity * height)
    # Avoid cancellation for a fast descending item close to the ground.
    return ((velocity + root) / gravity if velocity >= 0
            else 2 * height / (root - velocity))


def flight(height: float, velocity: float, elapsed: float, gravity: float
           ) -> tuple[float, float]:
    """Advance no further than contact; callers own the collision response."""
    contact = contact_time(height, velocity, gravity)
    if not math.isfinite(elapsed) or elapsed < 0 or elapsed > contact + 1e-9:
        raise ValueError("Flight interval crosses ground contact")
    return (max(0.0, height + velocity * elapsed - gravity * elapsed**2 / 2),
            velocity - gravity * elapsed)
