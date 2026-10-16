"""Bind the existing balance catalogue to the pure World motion policy."""

from ..pet.balance import BALANCE, BalanceCatalog
from ..world.motion import MotionParameters


def motion_parameters(catalog: BalanceCatalog = BALANCE) -> MotionParameters:
    def value(key: str) -> float:
        return catalog.number("object_behavior", key)

    return MotionParameters(
        value("fall_gravity"), value("bounce_restitution_fraction"),
        value("bounce_horizontal_damping_fraction"), value("bounce_inward_factor"),
        value("bounce_minimum_speed"), value("bounce_settling_speed"),
        catalog.integer("object_behavior", "bounce_maximum_contacts"),
        value("bounce_maximum_seconds"),
    )
